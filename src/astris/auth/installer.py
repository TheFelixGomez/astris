from pathlib import Path

AUTH_MODEL_TEMPLATE = """from astris.database import Field, SQLModel


class UserBase(SQLModel):
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str = Field()


class UserLogin(SQLModel):
    email: str
    password: str
    remember: bool = False


class UserRegister(SQLModel):
    name: str
    email: str
    password: str
    password_confirmation: str


class ProfileUpdate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=3, max_length=255)


class PasswordUpdate(SQLModel):
    current_password: str
    new_password: str = Field(min_length=8)
    new_password_confirmation: str
"""

AUTH_SERVICE_TEMPLATE = """from app.modules.auth.auth_model import User, UserRegister
from astris.auth import hash_password, verify_and_update_password, verify_password
from astris.database import Session, select


class AuthService:
    @staticmethod
    def authenticate(session: Session, email: str, password: str) -> User | None:
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            return None
        valid, updated_hash = verify_and_update_password(password, user.hashed_password)
        if not valid:
            return None
        if updated_hash:
            user.hashed_password = updated_hash
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

    @staticmethod
    def register(session: Session, data: UserRegister) -> User:
        hashed = hash_password(data.password)
        user = User(
            name=data.name.strip(),
            email=data.email.strip().lower(),
            hashed_password=hashed,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @staticmethod
    def email_exists(
        session: Session, email: str, exclude_user_id: int | None = None
    ) -> bool:
        stmt = select(User).where(User.email == email.strip().lower())
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)
        return session.exec(stmt).first() is not None

    @staticmethod
    def update_profile(
        session: Session, user_id: int, name: str, email: str
    ) -> User | None:
        user = session.get(User, user_id)
        if not user:
            return None
        user.name = name.strip()
        user.email = email.strip().lower()
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @staticmethod
    def update_password(
        session: Session, user_id: int, current_password: str, new_password: str
    ) -> bool:
        user = session.get(User, user_id)
        if not user:
            return False
        if not verify_password(current_password, user.hashed_password):
            return False
        user.hashed_password = hash_password(new_password)
        session.add(user)
        session.commit()
        return True
"""

AUTH_CONTROLLER_TEMPLATE = """from app.modules.auth.auth_model import (
    PasswordUpdate,
    ProfileUpdate,
    UserLogin,
    UserRegister,
)
from app.modules.auth.auth_service import AuthService
from astris.auth import (
    AuthUserId,
    auth_required,
    guest_required,
    login_user,
    logout_user,
)
from astris.database import DatabaseSession
from astris.http import HTTPException, RedirectResponse, Request
from astris.inertia import InertiaResponse, flash
from astris.routing import Controller

controller = Controller(tags=["Auth"])


@controller.get("/login", dependencies=[guest_required])
async def login_page(request: Request) -> InertiaResponse:
    return InertiaResponse(request, "Auth/Login")


@controller.post("/login", dependencies=[guest_required])
async def login(
    request: Request, data: UserLogin, db: DatabaseSession
) -> RedirectResponse:
    user = AuthService.authenticate(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=422,
            detail={"error": "These credentials do not match our records."},
        )

    login_user(request, user)
    flash(request, "success", f"Welcome back, {user.name}!")
    return RedirectResponse(url="/dashboard", status_code=303)


@controller.get("/register", dependencies=[guest_required])
async def register_page(request: Request) -> InertiaResponse:
    return InertiaResponse(request, "Auth/Register")


@controller.post("/register", dependencies=[guest_required])
async def register(
    request: Request, data: UserRegister, db: DatabaseSession
) -> RedirectResponse:
    if data.password != data.password_confirmation:
        raise HTTPException(
            status_code=422,
            detail={
                "password_confirmation": "The password confirmation does not match."
            },
        )

    if AuthService.email_exists(db, data.email):
        raise HTTPException(
            status_code=422,
            detail={"email": "An account with this email already exists."},
        )

    user = AuthService.register(db, data)
    login_user(request, user)
    flash(request, "success", f"Welcome to Astris, {user.name}!")
    return RedirectResponse(url="/dashboard", status_code=303)


@controller.post("/logout")
async def logout(request: Request) -> RedirectResponse:
    logout_user(request)
    flash(request, "info", "You have been logged out.")
    return RedirectResponse(url="/login", status_code=303)


@controller.get("/dashboard", dependencies=[auth_required])
async def dashboard(
    request: Request, user_id: AuthUserId, db: DatabaseSession
) -> InertiaResponse:
    from app.modules.tasks.task_service import TaskService

    tasks = TaskService.list_for_user(db, int(user_id))
    return InertiaResponse(
        request,
        "Dashboard",
        props={"tasks": tasks},
    )


@controller.post("/profile", dependencies=[auth_required])
async def update_profile(
    request: Request,
    data: ProfileUpdate,
    user_id: AuthUserId,
    db: DatabaseSession,
) -> RedirectResponse:
    uid = int(user_id)
    if AuthService.email_exists(db, data.email, exclude_user_id=uid):
        raise HTTPException(
            status_code=422,
            detail={"email": "This email is already in use by another account."},
        )

    user = AuthService.update_profile(db, uid, data.name, data.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    login_user(request, user)
    flash(request, "success", "Profile updated successfully!")
    return RedirectResponse(url="/dashboard", status_code=303)


@controller.post("/password", dependencies=[auth_required])
async def update_password(
    request: Request,
    data: PasswordUpdate,
    user_id: AuthUserId,
    db: DatabaseSession,
) -> RedirectResponse:
    if data.new_password != data.new_password_confirmation:
        raise HTTPException(
            status_code=422,
            detail={
                "new_password_confirmation": "The password confirmation does not match."
            },
        )

    success = AuthService.update_password(
        db, int(user_id), data.current_password, data.new_password
    )
    if not success:
        raise HTTPException(
            status_code=422,
            detail={
                "current_password": "The provided password does not match your current password."
            },
        )

    flash(request, "success", "Password updated successfully!")
    return RedirectResponse(url="/dashboard", status_code=303)
"""

TASK_MODEL_TEMPLATE = """from datetime import datetime
from astris.database import Field, SQLModel


class TaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    completed: bool = Field(default=False)


class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskCreate(SQLModel):
    title: str = Field(min_length=1, max_length=255)
"""

TASK_SERVICE_TEMPLATE = """from app.modules.tasks.task_model import Task, TaskCreate
from astris.database import Session, desc, select


class TaskService:
    @staticmethod
    def list_for_user(session: Session, user_id: int) -> list[Task]:
        return list(
            session.exec(
                select(Task)
                .where(Task.user_id == user_id)
                .order_by(desc(Task.created_at))
            ).all()
        )

    @staticmethod
    def create(session: Session, user_id: int, data: TaskCreate) -> Task:
        task = Task(title=data.title.strip(), user_id=user_id)
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def toggle(session: Session, user_id: int, task_id: int) -> Task | None:
        task = session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        ).first()
        if not task:
            return None
        task.completed = not task.completed
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def delete(session: Session, user_id: int, task_id: int) -> bool:
        task = session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        ).first()
        if not task:
            return False
        session.delete(task)
        session.commit()
        return True
"""

TASK_CONTROLLER_TEMPLATE = """from app.modules.tasks.task_model import TaskCreate
from app.modules.tasks.task_service import TaskService
from astris.auth import AuthUserId, auth_required
from astris.database import DatabaseSession
from astris.http import HTTPException, RedirectResponse, Request
from astris.inertia import flash
from astris.routing import Controller

controller = Controller(
    prefix="/tasks", tags=["Tasks"], dependencies=[auth_required]
)


@controller.post("")
async def create(
    request: Request,
    data: TaskCreate,
    user_id: AuthUserId,
    db: DatabaseSession,
) -> RedirectResponse:
    clean_title = data.title.strip()
    if not clean_title:
        raise HTTPException(
            status_code=422,
            detail={"title": "Task title cannot be empty."},
        )

    TaskService.create(db, int(user_id), data)
    flash(request, "success", "Task added successfully!")
    return RedirectResponse(url="/dashboard", status_code=303)


@controller.post("/{task_id}/toggle")
async def toggle(
    request: Request,
    task_id: int,
    user_id: AuthUserId,
    db: DatabaseSession,
) -> RedirectResponse:
    task = TaskService.toggle(db, int(user_id), task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    status_label = "completed" if task.completed else "reopened"
    flash(request, "success", f"Task marked as {status_label}!")
    return RedirectResponse(url="/dashboard", status_code=303)


@controller.delete("/{task_id}")
async def delete(
    request: Request,
    task_id: int,
    user_id: AuthUserId,
    db: DatabaseSession,
) -> RedirectResponse:
    success = TaskService.delete(db, int(user_id), task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found.")

    flash(request, "info", "Task removed.")
    return RedirectResponse(url="/dashboard", status_code=303)
"""

ASTRIS_LOGO_VUE_TEMPLATE = """<template>
  <svg
    viewBox="0 0 792 792"
    fill="currentColor"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="m50 757h88.8l37.8-92.3c-31.4-1.6-59-6.3-82.4-14.2z"/>
    <path d="m596.3 550.8q-11 6.5-22.3 12.6l79.1 193.6h88.9l-98.1-236.5q-22.4 15.6-47.6 30.3z"/>
    <path d="m210.1 582.6l185.9-454.7 147.5 360.9c25-14.4 48-29.9 68.2-46l-169.2-407.8h-93l-221.6 534.1c21.2 8.3 49.5 12.9 82.2 13.5z"/>
    <path fill-rule="evenodd" d="m372.5 466.8l23.5 76.4 23.5-76.4 69-23.5-68.8-23.8-23.7-75.8-23.7 75.8-68.8 23.8 69 23.5z"/>
    <path d="m756.2 309.9c-18.3-50.9-96.5-72.1-201.4-61.6 81.6-3.1 141.7 15.8 156.8 58 26.6 74.2-96.3 192.3-273.9 256.1-177.7 63.7-343.3 55.2-370-19-15.5-43.4 19.7-99.6 87.1-151.5-90.4 60.9-137.6 131.1-118.9 183.2 29.4 82 214.3 90.6 413.1 19.3 198.8-71.3 336.6-202.5 307.2-284.5z"/>
    <path d="m90 533.2c2.1 6 5.3 11.5 9.4 16.6q-2.3-3.9-3.9-8.2c-12.7-35.5 18.2-82.5 77.1-127.1l12.8-31c-71.7 50.7-110.7 107.1-95.4 149.7z"/>
    <path d="m437 275.7c-30 6.8-61.1 15.9-92.6 27.2q-0.3 0.1-0.6 0.2l-10.1 24.7q8.5-3.3 17.3-6.4c31.8-11.4 63.2-20.7 93.3-27.8l-7.4-17.9z"/>
    <path d="m688.7 323.7q1.4 4.1 2.1 8.4c0-6.6-1.1-12.9-3.2-18.9-13.1-36.3-63.2-53.7-132.2-52.9l7 16.8c66.6-1.8 114.4 13.4 126.3 46.6z"/>
  </svg>
</template>
"""

VUE_LOGIN_TEMPLATE = """<script setup lang="ts">
import { useForm, Link } from '@inertiajs/vue3'
import AstrisLogo from '../../Components/AstrisLogo.vue'

const form = useForm({
  email: '',
  password: '',
  remember: false,
})

const submit = () => {
  form.post('/login', {
    onFinish: () => form.reset('password'),
  })
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-100 font-sans relative selection:bg-sky-500 selection:text-white">
    <!-- Subtle Background Glow -->
    <div class="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-sky-500/10 blur-[100px] rounded-full pointer-events-none -z-10"></div>

    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="flex justify-center">
        <Link href="/" class="p-3 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur shadow-xl hover:border-sky-500/40 transition duration-200">
          <AstrisLogo class="w-10 h-10 text-sky-400" />
        </Link>
      </div>
      <h2 class="mt-4 text-center text-3xl font-extrabold tracking-tight text-white">
        Sign in to your account
      </h2>
      <p class="mt-2 text-center text-sm text-slate-400">
        Or
        <Link href="/register" class="font-medium text-sky-400 hover:text-sky-300 underline underline-offset-4 transition">
          create a new account
        </Link>
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-slate-900/80 backdrop-blur border border-slate-800 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
        <form @submit.prevent="submit" class="space-y-6">
          <div
            v-if="form.errors.error"
            class="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-sm text-rose-400 flex items-center gap-2"
          >
            <svg class="w-4 h-4 shrink-0 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{{ form.errors.error }}</span>
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-slate-300">Email address</label>
            <div class="mt-1">
              <input
                id="email"
                v-model="form.email"
                type="email"
                autocomplete="email"
                required
                class="appearance-none block w-full px-3.5 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition text-sm"
                placeholder="you@example.com"
              />
            </div>
            <p v-if="form.errors.email" class="mt-2 text-sm text-rose-400">{{ form.errors.email }}</p>
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-slate-300">Password</label>
            <div class="mt-1">
              <input
                id="password"
                v-model="form.password"
                type="password"
                autocomplete="current-password"
                required
                class="appearance-none block w-full px-3.5 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition text-sm"
                placeholder="••••••••"
              />
            </div>
            <p v-if="form.errors.password" class="mt-2 text-sm text-rose-400">{{ form.errors.password }}</p>
          </div>

          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <input
                id="remember"
                v-model="form.remember"
                type="checkbox"
                class="h-4 w-4 text-sky-500 focus:ring-sky-400 border-slate-700 rounded bg-slate-800"
              />
              <label for="remember" class="ml-2 block text-sm text-slate-400">Remember me</label>
            </div>
          </div>

          <div>
            <button
              type="submit"
              :disabled="form.processing"
              class="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-xl shadow-md text-sm font-semibold text-white bg-sky-500 hover:bg-sky-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 disabled:opacity-50 transition duration-200"
            >
              <span v-if="form.processing">Signing in...</span>
              <span v-else>Sign In</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
"""

VUE_REGISTER_TEMPLATE = """<script setup lang="ts">
import { useForm, Link } from '@inertiajs/vue3'
import AstrisLogo from '../../Components/AstrisLogo.vue'

const form = useForm({
  name: '',
  email: '',
  password: '',
  password_confirmation: '',
})

const submit = () => {
  form.post('/register', {
    onFinish: () => form.reset('password', 'password_confirmation'),
  })
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-100 font-sans relative selection:bg-sky-500 selection:text-white">
    <!-- Subtle Background Glow -->
    <div class="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[300px] bg-sky-500/10 blur-[100px] rounded-full pointer-events-none -z-10"></div>

    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="flex justify-center">
        <Link href="/" class="p-3 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur shadow-xl hover:border-sky-500/40 transition duration-200">
          <AstrisLogo class="w-10 h-10 text-sky-400" />
        </Link>
      </div>
      <h2 class="mt-4 text-center text-3xl font-extrabold tracking-tight text-white">
        Create a new account
      </h2>
      <p class="mt-2 text-center text-sm text-slate-400">
        Already have an account?
        <Link href="/login" class="font-medium text-sky-400 hover:text-sky-300 underline underline-offset-4 transition">
          Sign in
        </Link>
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-slate-900/80 backdrop-blur border border-slate-800 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
        <form @submit.prevent="submit" class="space-y-6">
          <div>
            <label for="name" class="block text-sm font-medium text-slate-300">Full Name</label>
            <div class="mt-1">
              <input
                id="name"
                v-model="form.name"
                type="text"
                autocomplete="name"
                required
                class="appearance-none block w-full px-3.5 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition text-sm"
                placeholder="Jane Doe"
              />
            </div>
            <p v-if="form.errors.name" class="mt-2 text-sm text-rose-400">{{ form.errors.name }}</p>
          </div>

          <div>
            <label for="email" class="block text-sm font-medium text-slate-300">Email address</label>
            <div class="mt-1">
              <input
                id="email"
                v-model="form.email"
                type="email"
                autocomplete="email"
                required
                class="appearance-none block w-full px-3.5 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition text-sm"
                placeholder="you@example.com"
              />
            </div>
            <p v-if="form.errors.email" class="mt-2 text-sm text-rose-400">{{ form.errors.email }}</p>
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-slate-300">Password</label>
            <div class="mt-1">
              <input
                id="password"
                v-model="form.password"
                type="password"
                autocomplete="new-password"
                required
                class="appearance-none block w-full px-3.5 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition text-sm"
                placeholder="••••••••"
              />
            </div>
            <p v-if="form.errors.password" class="mt-2 text-sm text-rose-400">{{ form.errors.password }}</p>
          </div>

          <div>
            <label for="password_confirmation" class="block text-sm font-medium text-slate-300">Confirm Password</label>
            <div class="mt-1">
              <input
                id="password_confirmation"
                v-model="form.password_confirmation"
                type="password"
                autocomplete="new-password"
                required
                class="appearance-none block w-full px-3.5 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition text-sm"
                placeholder="••••••••"
              />
            </div>
            <p v-if="form.errors.password_confirmation" class="mt-2 text-sm text-rose-400">{{ form.errors.password_confirmation }}</p>
          </div>

          <div>
            <button
              type="submit"
              :disabled="form.processing"
              class="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-xl shadow-md text-sm font-semibold text-white bg-sky-500 hover:bg-sky-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 disabled:opacity-50 transition duration-200"
            >
              <span v-if="form.processing">Creating account...</span>
              <span v-else>Register</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
"""

VUE_DASHBOARD_TEMPLATE = """<script setup lang="ts">
import { ref, computed } from 'vue'
import { usePage, router, Link, useForm } from '@inertiajs/vue3'
import AstrisLogo from '../Components/AstrisLogo.vue'

interface Task {
  id: number
  title: string
  completed: boolean
  created_at: string
}

interface Props {
  tasks?: Task[]
}

const props = withDefaults(defineProps<Props>(), {
  tasks: () => [],
})

const page = usePage()
const activeTab = ref<'tasks' | 'profile' | 'info'>('tasks')

// --- Tasks CRUD ---
const taskForm = useForm({
  title: '',
})

const submitTask = () => {
  if (!taskForm.title.trim()) return
  taskForm.post('/tasks', {
    preserveScroll: true,
    onSuccess: () => taskForm.reset('title'),
  })
}

const toggleTask = (task: Task) => {
  router.post(`/tasks/${task.id}/toggle`, {}, { preserveScroll: true })
}

const deleteTask = (task: Task) => {
  router.delete(`/tasks/${task.id}`, { preserveScroll: true })
}

const completedCount = computed(() => {
  return props.tasks.filter((t) => t.completed).length
})

// --- Profile Update ---
const profileForm = useForm({
  name: page.props.auth?.user?.name || '',
  email: page.props.auth?.user?.email || '',
})

const updateProfile = () => {
  profileForm.post('/profile', {
    preserveScroll: true,
  })
}

// --- Password Update ---
const passwordForm = useForm({
  current_password: '',
  new_password: '',
  new_password_confirmation: '',
})

const updatePassword = () => {
  passwordForm.post('/password', {
    preserveScroll: true,
    onSuccess: () => passwordForm.reset(),
  })
}

const logout = () => {
  router.post('/logout')
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 font-sans relative selection:bg-sky-500 selection:text-white">
    <!-- Subtle Background Ambient Glow -->
    <div class="absolute top-0 right-1/4 w-[600px] h-[300px] bg-sky-500/10 blur-[140px] rounded-full pointer-events-none -z-10"></div>

    <!-- Navigation Header -->
    <nav class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <Link href="/" class="flex items-center space-x-3 group">
            <AstrisLogo class="w-8 h-8 text-sky-400 group-hover:scale-105 transition duration-200" />
            <span class="font-bold text-lg text-white">Astris App</span>
          </Link>
          <div class="flex items-center space-x-4">
            <div class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs font-medium text-slate-300">
              <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
              {{ page.props.auth?.user?.name || page.props.auth?.user?.email }}
            </div>
            <button
              @click="logout"
              class="px-3.5 py-1.5 rounded-xl text-xs font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition duration-200"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Main Workspace -->
    <main class="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <!-- Flash Messages -->
      <div
        v-if="page.props.flash?.success"
        class="mb-6 p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center gap-2.5 shadow-sm"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <span>{{ page.props.flash.success }}</span>
      </div>

      <div
        v-if="page.props.flash?.info"
        class="mb-6 p-4 rounded-2xl bg-sky-500/10 border border-sky-500/30 text-sky-400 text-sm flex items-center gap-2.5 shadow-sm"
      >
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span>{{ page.props.flash.info }}</span>
      </div>

      <!-- Welcome Greeting and Tab Selector -->
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <h1 class="text-2xl sm:text-3xl font-extrabold text-white">
            Welcome, {{ page.props.auth?.user?.name || 'Developer' }}!
          </h1>
          <p class="text-sm text-slate-400 mt-1">
            Full-stack reactivity with SQLModel, Inertia, and Python.
          </p>
        </div>

        <!-- Tab Controls -->
        <div class="inline-flex p-1 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur self-start md:self-auto">
          <button
            @click="activeTab = 'tasks'"
            :class="[
              'px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2',
              activeTab === 'tasks'
                ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-white'
            ]"
          >
            <span>Tasks</span>
            <span
              :class="[
                'px-1.5 py-0.5 rounded-md text-[10px] font-mono',
                activeTab === 'tasks' ? 'bg-sky-600 text-white' : 'bg-slate-800 text-slate-300'
              ]"
            >
              {{ completedCount }}/{{ props.tasks.length }}
            </span>
          </button>
          <button
            @click="activeTab = 'profile'"
            :class="[
              'px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5',
              activeTab === 'profile'
                ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-white'
            ]"
          >
            Profile & Security
          </button>
          <button
            @click="activeTab = 'info'"
            :class="[
              'px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-1.5',
              activeTab === 'info'
                ? 'bg-sky-500 text-white shadow-md shadow-sky-500/20'
                : 'text-slate-400 hover:text-white'
            ]"
          >
            System Info
          </button>
        </div>
      </div>

      <!-- TAB 1: Tasks CRUD -->
      <div v-if="activeTab === 'tasks'" class="space-y-6">
        <!-- New Task Form Card -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur">
          <h2 class="text-lg font-bold text-white mb-2 flex items-center gap-2">
            <span>✨</span> Add a New Task
          </h2>
          <p class="text-xs text-slate-400 mb-5">
            Submit a task to see real-time SQLModel persistence and Inertia page updates without writing API client code.
          </p>

          <form @submit.prevent="submitTask" class="flex flex-col sm:flex-row gap-3">
            <div class="flex-1">
              <input
                v-model="taskForm.title"
                type="text"
                placeholder="What needs to be done? Type and press Enter..."
                required
                class="w-full px-4 py-3 rounded-2xl bg-slate-800/80 border border-slate-700/80 text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition"
              />
              <p v-if="taskForm.errors.title" class="mt-2 text-xs text-rose-400">
                {{ taskForm.errors.title }}
              </p>
            </div>
            <button
              type="submit"
              :disabled="taskForm.processing || !taskForm.title.trim()"
              class="px-6 py-3 rounded-2xl bg-sky-500 hover:bg-sky-400 text-white text-sm font-semibold shadow-md shadow-sky-500/20 disabled:opacity-50 transition duration-200 shrink-0 flex items-center justify-center gap-2"
            >
              <span v-if="taskForm.processing">Saving...</span>
              <span v-else>Add Task</span>
            </button>
          </form>
        </div>

        <!-- Task List Card -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-bold text-white flex items-center gap-2">
              <span>📋</span> Your Tasks
            </h2>
            <span class="text-xs font-mono text-slate-400">
              {{ props.tasks.length }} {{ props.tasks.length === 1 ? 'item' : 'items' }}
            </span>
          </div>

          <!-- Empty State -->
          <div
            v-if="props.tasks.length === 0"
            class="text-center py-12 px-4 rounded-2xl border border-dashed border-slate-800 bg-slate-900/40"
          >
            <div class="w-12 h-12 rounded-2xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400 text-xl mx-auto mb-3">
              💡
            </div>
            <h3 class="text-sm font-semibold text-white">No tasks created yet</h3>
            <p class="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Add your first task above to test SQLite database writes, reactive Inertia updates, and session handling.
            </p>
          </div>

          <!-- Task Items -->
          <div v-else class="space-y-2.5">
            <div
              v-for="task in props.tasks"
              :key="task.id"
              :class="[
                'group p-4 rounded-2xl border transition duration-200 flex items-center justify-between gap-3',
                task.completed
                  ? 'bg-slate-900/40 border-slate-800/60 opacity-60'
                  : 'bg-slate-800/40 hover:bg-slate-800/70 border-slate-700/60'
              ]"
            >
              <div class="flex items-center gap-3.5 flex-1 min-w-0">
                <button
                  type="button"
                  @click="toggleTask(task)"
                  :class="[
                    'w-5 h-5 rounded-lg border flex items-center justify-center transition shrink-0',
                    task.completed
                      ? 'bg-emerald-500 border-emerald-400 text-white'
                      : 'border-slate-600 hover:border-sky-400 bg-slate-800'
                  ]"
                >
                  <svg v-if="task.completed" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                  </svg>
                </button>
                <span
                  :class="[
                    'text-sm truncate select-none',
                    task.completed ? 'line-through text-slate-500' : 'text-slate-200'
                  ]"
                >
                  {{ task.title }}
                </span>
              </div>

              <div class="flex items-center gap-3 shrink-0">
                <span v-if="task.created_at" class="text-[11px] font-mono text-slate-500 hidden sm:inline">
                  {{ formatDate(task.created_at) }}
                </span>
                <button
                  type="button"
                  @click="deleteTask(task)"
                  class="p-1.5 rounded-xl text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                  title="Delete Task"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 2: Profile & Security -->
      <div v-else-if="activeTab === 'profile'" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Profile Info Card -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur">
          <h2 class="text-lg font-bold text-white mb-2 flex items-center gap-2">
            <span>👤</span> Profile Information
          </h2>
          <p class="text-xs text-slate-400 mb-6">
            Update your account's display name and primary email address.
          </p>

          <form @submit.prevent="updateProfile" class="space-y-4">
            <div>
              <label for="name" class="block text-xs font-medium text-slate-300 mb-1">Display Name</label>
              <input
                id="name"
                v-model="profileForm.name"
                type="text"
                required
                class="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition"
              />
              <p v-if="profileForm.errors.name" class="mt-1.5 text-xs text-rose-400">
                {{ profileForm.errors.name }}
              </p>
            </div>

            <div>
              <label for="email" class="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
              <input
                id="email"
                v-model="profileForm.email"
                type="email"
                required
                class="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition"
              />
              <p v-if="profileForm.errors.email" class="mt-1.5 text-xs text-rose-400">
                {{ profileForm.errors.email }}
              </p>
            </div>

            <div class="pt-2">
              <button
                type="submit"
                :disabled="profileForm.processing"
                class="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-sm font-semibold shadow-md shadow-sky-500/20 disabled:opacity-50 transition duration-200"
              >
                <span v-if="profileForm.processing">Saving...</span>
                <span v-else>Save Profile</span>
              </button>
            </div>
          </form>
        </div>

        <!-- Password Update Card -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur">
          <h2 class="text-lg font-bold text-white mb-2 flex items-center gap-2">
            <span>🔒</span> Update Password
          </h2>
          <p class="text-xs text-slate-400 mb-6">
            Ensure your account is using a secure Argon2id hashed password.
          </p>

          <form @submit.prevent="updatePassword" class="space-y-4">
            <div>
              <label for="current_password" class="block text-xs font-medium text-slate-300 mb-1">Current Password</label>
              <input
                id="current_password"
                v-model="passwordForm.current_password"
                type="password"
                required
                class="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition"
              />
              <p v-if="passwordForm.errors.current_password" class="mt-1.5 text-xs text-rose-400">
                {{ passwordForm.errors.current_password }}
              </p>
            </div>

            <div>
              <label for="new_password" class="block text-xs font-medium text-slate-300 mb-1">New Password</label>
              <input
                id="new_password"
                v-model="passwordForm.new_password"
                type="password"
                required
                class="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition"
              />
              <p v-if="passwordForm.errors.new_password" class="mt-1.5 text-xs text-rose-400">
                {{ passwordForm.errors.new_password }}
              </p>
            </div>

            <div>
              <label for="new_password_confirmation" class="block text-xs font-medium text-slate-300 mb-1">Confirm New Password</label>
              <input
                id="new_password_confirmation"
                v-model="passwordForm.new_password_confirmation"
                type="password"
                required
                class="w-full px-3.5 py-2.5 rounded-xl bg-slate-800/80 border border-slate-700/80 text-white text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition"
              />
              <p v-if="passwordForm.errors.new_password_confirmation" class="mt-1.5 text-xs text-rose-400">
                {{ passwordForm.errors.new_password_confirmation }}
              </p>
            </div>

            <div class="pt-2">
              <button
                type="submit"
                :disabled="passwordForm.processing"
                class="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-white text-sm font-semibold shadow-md shadow-sky-500/20 disabled:opacity-50 transition duration-200"
              >
                <span v-if="passwordForm.processing">Updating...</span>
                <span v-else>Update Password</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- TAB 3: System Info & Docs -->
      <div v-else-if="activeTab === 'info'" class="space-y-6">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-5">
          <div class="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-2xl backdrop-blur">
            <div class="text-xs font-medium text-slate-400 uppercase tracking-wider">Session Status</div>
            <div class="mt-2 text-xl font-bold text-emerald-400 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]"></span>
              Authenticated
            </div>
            <p class="mt-2 text-xs text-slate-400">Signed HTTP-only cookie with CSRF defense.</p>
          </div>

          <div class="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-2xl backdrop-blur">
            <div class="text-xs font-medium text-slate-400 uppercase tracking-wider">Database Engine</div>
            <div class="mt-2 text-xl font-bold text-white flex items-center gap-2">
              <span>🗄️</span> SQLite
            </div>
            <p class="mt-2 text-xs text-slate-400">Managed with SQLModel and Orbit migrations.</p>
          </div>

          <div class="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-2xl backdrop-blur">
            <div class="text-xs font-medium text-slate-400 uppercase tracking-wider">Frontend Stack</div>
            <div class="mt-2 text-xl font-bold text-sky-400 flex items-center gap-2">
              <span>⚡</span> Vue 3 + Tailwind v4
            </div>
            <p class="mt-2 text-xs text-slate-400">Powered by Vite and the Inertia.js protocol.</p>
          </div>
        </div>

        <!-- Quick Links and Cheatsheet -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur">
          <h2 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span>🛠️</span> Orbit CLI Cheatsheet
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div class="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80">
              <div class="text-slate-400 mb-1">// Scaffold a complete domain module</div>
              <code class="text-sky-400">uv run orbit make:module billing</code>
            </div>
            <div class="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80">
              <div class="text-slate-400 mb-1">// Auto-generate a schema migration</div>
              <code class="text-sky-400">uv run orbit make:migration "create_table"</code>
            </div>
            <div class="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80">
              <div class="text-slate-400 mb-1">// Apply pending migrations</div>
              <code class="text-sky-400">uv run orbit migrate</code>
            </div>
            <div class="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80">
              <div class="text-slate-400 mb-1">// Explore API docs</div>
              <code class="text-sky-400">http://localhost:8000/docs</code>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
"""


def install_auth_starter(base_path: Path | None = None, force: bool = False) -> None:
    """Install a full-stack authentication starter kit (models, services, controllers, and Vue pages)."""
    root = base_path or Path.cwd()

    auth_module_dir = root / "app" / "modules" / "auth"
    tasks_module_dir = root / "app" / "modules" / "tasks"
    auth_pages_dir = root / "resources" / "js" / "Pages" / "Auth"
    dashboard_file = root / "resources" / "js" / "Pages" / "Dashboard.vue"

    target_files = [
        auth_module_dir / "auth_model.py",
        auth_module_dir / "auth_service.py",
        auth_module_dir / "auth_controller.py",
        tasks_module_dir / "task_model.py",
        tasks_module_dir / "task_service.py",
        tasks_module_dir / "task_controller.py",
        auth_pages_dir / "Login.vue",
        auth_pages_dir / "Register.vue",
        dashboard_file,
    ]

    existing_files = [f for f in target_files if f.exists()]
    if existing_files and not force:
        file_list = ", ".join(f.name for f in existing_files)
        raise FileExistsError(
            f"Authentication files already exist ({file_list}). Use --force to overwrite."
        )

    # 1. Backend module: app/modules/auth/
    auth_module_dir.mkdir(parents=True, exist_ok=True)
    (auth_module_dir / "__init__.py").touch()

    (auth_module_dir / "auth_model.py").write_text(
        AUTH_MODEL_TEMPLATE, encoding="utf-8"
    )
    (auth_module_dir / "auth_service.py").write_text(
        AUTH_SERVICE_TEMPLATE, encoding="utf-8"
    )
    (auth_module_dir / "auth_controller.py").write_text(
        AUTH_CONTROLLER_TEMPLATE, encoding="utf-8"
    )

    # 2. Backend module: app/modules/tasks/
    tasks_module_dir.mkdir(parents=True, exist_ok=True)
    (tasks_module_dir / "__init__.py").touch()

    (tasks_module_dir / "task_model.py").write_text(
        TASK_MODEL_TEMPLATE, encoding="utf-8"
    )
    (tasks_module_dir / "task_service.py").write_text(
        TASK_SERVICE_TEMPLATE, encoding="utf-8"
    )
    (tasks_module_dir / "task_controller.py").write_text(
        TASK_CONTROLLER_TEMPLATE, encoding="utf-8"
    )

    # 3. Components: resources/js/Components/AstrisLogo.vue
    components_dir = root / "resources" / "js" / "Components"
    components_dir.mkdir(parents=True, exist_ok=True)
    logo_file = components_dir / "AstrisLogo.vue"
    if not logo_file.exists():
        logo_file.write_text(ASTRIS_LOGO_VUE_TEMPLATE, encoding="utf-8")

    # 4. Frontend pages: resources/js/Pages/Auth/
    auth_pages_dir.mkdir(parents=True, exist_ok=True)

    (auth_pages_dir / "Login.vue").write_text(VUE_LOGIN_TEMPLATE, encoding="utf-8")
    (auth_pages_dir / "Register.vue").write_text(
        VUE_REGISTER_TEMPLATE, encoding="utf-8"
    )

    pages_dir = root / "resources" / "js" / "Pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    dashboard_file.write_text(VUE_DASHBOARD_TEMPLATE, encoding="utf-8")
