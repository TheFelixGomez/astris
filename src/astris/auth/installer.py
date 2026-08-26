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
"""

AUTH_SERVICE_TEMPLATE = """from app.modules.auth.auth_model import User, UserRegister
from astris.auth import hash_password, verify_and_update_password
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
            name=data.name,
            email=data.email,
            hashed_password=hashed,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @staticmethod
    def email_exists(session: Session, email: str) -> bool:
        return session.exec(select(User).where(User.email == email)).first() is not None
"""

AUTH_CONTROLLER_TEMPLATE = """from app.modules.auth.auth_model import UserLogin, UserRegister
from app.modules.auth.auth_service import AuthService
from astris.auth import auth_required, guest_required, login_user, logout_user
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
async def dashboard(request: Request) -> InertiaResponse:
    return InertiaResponse(request, "Dashboard")
"""

VUE_LOGIN_TEMPLATE = """<script setup lang="ts">
import { useForm, Link } from '@inertiajs/vue3'

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
  <div class="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-100 font-sans">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="flex justify-center">
        <span class="text-4xl">⚡</span>
      </div>
      <h2 class="mt-4 text-center text-3xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
        Sign in to your account
      </h2>
      <p class="mt-2 text-center text-sm text-slate-400">
        Or
        <Link href="/register" class="font-medium text-blue-400 hover:text-blue-300 underline transition">
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
                class="appearance-none block w-full px-3 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-sm"
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
                class="appearance-none block w-full px-3 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-sm"
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
                class="h-4 w-4 text-blue-500 focus:ring-blue-400 border-slate-700 rounded bg-slate-800"
              />
              <label for="remember" class="ml-2 block text-sm text-slate-400">Remember me</label>
            </div>
          </div>

          <div>
            <button
              type="submit"
              :disabled="form.processing"
              class="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-xl shadow-md text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition"
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
  <div class="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-100 font-sans">
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="flex justify-center">
        <span class="text-4xl">⚡</span>
      </div>
      <h2 class="mt-4 text-center text-3xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
        Create a new account
      </h2>
      <p class="mt-2 text-center text-sm text-slate-400">
        Already have an account?
        <Link href="/login" class="font-medium text-blue-400 hover:text-blue-300 underline transition">
          Sign in
        </Link>
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="bg-slate-900/80 backdrop-blur border border-slate-800 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
        <form @submit.prevent="submit" class="space-y-5">
          <div>
            <label for="name" class="block text-sm font-medium text-slate-300">Full Name</label>
            <div class="mt-1">
              <input
                id="name"
                v-model="form.name"
                type="text"
                autocomplete="name"
                required
                class="appearance-none block w-full px-3 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-sm"
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
                class="appearance-none block w-full px-3 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-sm"
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
                class="appearance-none block w-full px-3 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-sm"
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
                class="appearance-none block w-full px-3 py-2.5 border border-slate-700 rounded-xl shadow-sm placeholder-slate-500 bg-slate-800/80 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-sm"
                placeholder="••••••••"
              />
            </div>
            <p v-if="form.errors.password_confirmation" class="mt-2 text-sm text-rose-400">{{ form.errors.password_confirmation }}</p>
          </div>

          <div>
            <button
              type="submit"
              :disabled="form.processing"
              class="w-full flex justify-center py-2.5 px-4 border border-transparent rounded-xl shadow-md text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition"
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
import { usePage, router } from '@inertiajs/vue3'

const page = usePage()

const logout = () => {
  router.post('/logout')
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 font-sans">
    <nav class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center space-x-3">
            <span class="text-2xl">⚡</span>
            <span class="font-bold text-lg text-white">Astris App</span>
          </div>
          <div class="flex items-center space-x-4">
            <span class="text-sm text-slate-300">{{ page.props.auth?.user?.name || page.props.auth?.user?.email }}</span>
            <button
              @click="logout"
              class="px-3.5 py-1.5 rounded-lg text-sm font-medium text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 transition"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </nav>

    <main class="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <div v-if="page.props.flash?.success" class="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm">
        {{ page.props.flash.success }}
      </div>

      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl">
        <h1 class="text-3xl font-extrabold text-white">Dashboard</h1>
        <p class="mt-2 text-slate-400">
          Welcome to your authenticated Astris dashboard!
        </p>

        <div class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="p-6 rounded-xl bg-slate-800/60 border border-slate-700/60">
            <div class="text-sm font-medium text-slate-400">Session Status</div>
            <div class="mt-2 text-2xl font-bold text-emerald-400">Authenticated ✓</div>
          </div>
          <div class="p-6 rounded-xl bg-slate-800/60 border border-slate-700/60">
            <div class="text-sm font-medium text-slate-400">User Email</div>
            <div class="mt-2 text-lg font-semibold text-white">{{ page.props.auth?.user?.email }}</div>
          </div>
          <div class="p-6 rounded-xl bg-slate-800/60 border border-slate-700/60">
            <div class="text-sm font-medium text-slate-400">Security</div>
            <div class="mt-2 text-lg font-semibold text-blue-400">Signed Cookies Active</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
"""


def install_auth_starter(base_path: Path | None = None) -> None:
    """Install a full-stack authentication starter kit (models, services, controllers, and Vue pages)."""
    root = base_path or Path.cwd()

    # 1. Backend module: app/modules/auth/
    auth_module_dir = root / "app" / "modules" / "auth"
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

    # 2. Frontend pages: resources/js/Pages/Auth/
    auth_pages_dir = root / "resources" / "js" / "Pages" / "Auth"
    auth_pages_dir.mkdir(parents=True, exist_ok=True)

    (auth_pages_dir / "Login.vue").write_text(VUE_LOGIN_TEMPLATE, encoding="utf-8")
    (auth_pages_dir / "Register.vue").write_text(
        VUE_REGISTER_TEMPLATE, encoding="utf-8"
    )

    pages_dir = root / "resources" / "js" / "Pages"
    (pages_dir / "Dashboard.vue").write_text(VUE_DASHBOARD_TEMPLATE, encoding="utf-8")
