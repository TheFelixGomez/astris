# CSRF Protection

Astris includes enterprise-grade **Cross-Site Request Forgery (CSRF)** protection enabled by default.

## How CSRF Protection Works

1. On every request, Astris sets a secure, readable cookie named **`XSRF-TOKEN`**.
2. Frontend libraries (such as Inertia.js and Axios) automatically extract `XSRF-TOKEN` from the cookie and send it in the **`X-XSRF-TOKEN`** header on mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`).
3. Astris's `CSRFMiddleware` verifies that the token in the header matches the secret token in the session cookie.
4. If invalid or missing, a `403 Forbidden` response is returned.

## Zero Frontend Setup

Because Astris sets the standard `XSRF-TOKEN` cookie, both **Inertia.js** and **Axios** automatically read the token and attach the `X-XSRF-TOKEN` header on every mutating request with zero configuration.

### 1. Inertia.js (`useForm`)
```vue
<script setup lang="ts">
import { useForm } from '@inertiajs/vue3'

const form = useForm({ email: '' })

// Automatically includes the X-XSRF-TOKEN header
const submit = () => form.post('/newsletter')
</script>
```

### 2. Axios (Raw API Calls)
Axios natively looks for the `XSRF-TOKEN` cookie by default:

```typescript
import axios from 'axios'

// Automatically reads XSRF-TOKEN cookie and sends X-XSRF-TOKEN header
const response = await axios.post('/api/data', { message: 'Hello' })
```

## Exempting Specific Routes

For external webhooks (e.g. Stripe, GitHub, Slack) that cannot send an XSRF cookie, exempt the path in `main.py`:

```python
from astris import Astris

app = Astris(
    csrf_exempt_paths=[
        "/api/webhooks/stripe",
        "/api/webhooks/github",
    ]
)
```

## Next Steps

* Configure session security: [Signed Cookie Sessions](/security/sessions).
* Explore the Orbit CLI: [Orbit CLI Reference](/cli/orbit).
