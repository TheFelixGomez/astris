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
import { usePage, router, Link } from '@inertiajs/vue3'
import AstrisLogo from '../Components/AstrisLogo.vue'

const page = usePage()

const logout = () => {
  router.post('/logout')
}
</script>

<template>
  <div class="min-h-screen bg-slate-950 text-slate-100 font-sans relative selection:bg-sky-500 selection:text-white">
    <!-- Subtle Background Ambient Glow -->
    <div class="absolute top-0 right-1/4 w-[500px] h-[250px] bg-sky-500/10 blur-[120px] rounded-full pointer-events-none -z-10"></div>

    <nav class="border-b border-slate-800 bg-slate-900/60 backdrop-blur sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16 items-center">
          <Link href="/" class="flex items-center space-x-3 group">
            <AstrisLogo class="w-8 h-8 text-sky-400 group-hover:scale-105 transition duration-200" />
            <span class="font-bold text-lg text-white">Astris App</span>
          </Link>
          <div class="flex items-center space-x-4">
            <div class="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-xs font-medium text-slate-300">
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

    <main class="max-w-7xl mx-auto py-10 px-4 sm:px-6 lg:px-8">
      <div v-if="page.props.flash?.success" class="mb-6 p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm flex items-center gap-2.5">
        <svg class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        <span>{{ page.props.flash.success }}</span>
      </div>

      <div class="bg-slate-900/80 border border-slate-800 rounded-3xl p-8 sm:p-10 shadow-2xl backdrop-blur">
        <h1 class="text-3xl font-extrabold text-white">Dashboard</h1>
        <p class="mt-2 text-slate-400">
          Welcome to your authenticated Astris application!
        </p>

        <div class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-5">
          <div class="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/60 shadow-sm">
            <div class="text-xs font-medium text-slate-400 uppercase tracking-wider">Session Status</div>
            <div class="mt-2 text-xl font-bold text-emerald-400 flex items-center gap-2">
              <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]"></span>
              Authenticated
            </div>
          </div>
          <div class="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/60 shadow-sm">
            <div class="text-xs font-medium text-slate-400 uppercase tracking-wider">User Email</div>
            <div class="mt-2 text-base font-semibold text-white truncate">{{ page.props.auth?.user?.email }}</div>
          </div>
          <div class="p-6 rounded-2xl bg-slate-800/50 border border-slate-700/60 shadow-sm">
            <div class="text-xs font-medium text-slate-400 uppercase tracking-wider">Security Engine</div>
            <div class="mt-2 text-base font-semibold text-sky-400 flex items-center gap-2">
              <span>🛡️</span>
              Signed Cookies & CSRF
            </div>
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

    # 2. Components: resources/js/Components/AstrisLogo.vue
    components_dir = root / "resources" / "js" / "Components"
    components_dir.mkdir(parents=True, exist_ok=True)
    logo_file = components_dir / "AstrisLogo.vue"
    if not logo_file.exists():
        logo_file.write_text(ASTRIS_LOGO_VUE_TEMPLATE, encoding="utf-8")

    # 3. Frontend pages: resources/js/Pages/Auth/
    auth_pages_dir = root / "resources" / "js" / "Pages" / "Auth"
    auth_pages_dir.mkdir(parents=True, exist_ok=True)

    (auth_pages_dir / "Login.vue").write_text(VUE_LOGIN_TEMPLATE, encoding="utf-8")
    (auth_pages_dir / "Register.vue").write_text(
        VUE_REGISTER_TEMPLATE, encoding="utf-8"
    )

    pages_dir = root / "resources" / "js" / "Pages"
    (pages_dir / "Dashboard.vue").write_text(VUE_DASHBOARD_TEMPLATE, encoding="utf-8")
