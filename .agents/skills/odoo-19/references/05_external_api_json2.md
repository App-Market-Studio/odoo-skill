# Odoo 19.0: External JSON-2 API Reference

Starting in **Odoo 19.0**, the primary interface for external integrations is the **External JSON-2 API** (`/json/2/`). The legacy `/xmlrpc`, `/xmlrpc/2`, and `/jsonrpc` endpoints are deprecated and scheduled for future removal.

---

## 1. Overview & Deprecation Notice

> [!WARNING]
> Both XML-RPC (`/xmlrpc`, `/xmlrpc/2`) and JSON-RPC (`/jsonrpc`) are deprecated in Odoo 19.0.
> All new external scripts, integrations, and microservices should target `POST /json/2/<model>/<method>`.

---

## 2. HTTP Request Format

To execute an ORM method externally, send an HTTP POST request to `/json/2/<model>/<method>`:

### Headers
| Header | Requirement | Description |
| :--- | :--- | :--- |
| `Host` | **Required** | Hostname of the target Odoo server |
| `Authorization` | **Required** | `bearer <api_key>` (User API Key generated from user preferences) |
| `Content-Type` | **Required** | `application/json; charset=utf-8` |
| `X-Odoo-Database` | Optional | Database name (required if multi-db hosting is active) |
| `User-Agent` | Recommended | Identifier of the calling client application |

### URL Path
- `<model>`: Technical model name (e.g. `res.partner`, `sale.order`, `estate.property`).
- `<method>`: Method to execute (e.g. `search_read`, `read`, `create`, `write`, `unlink`, or custom method).

---

## 3. Request Payload

### Calling `@api.model` Methods (e.g. `search_read`, `create`)
```json
{
    "context": {
        "lang": "en_US"
    },
    "domain": [["is_company", "=", true]],
    "fields": ["id", "name", "email", "phone"],
    "limit": 10
}
```

### Calling Recordset Methods (e.g. `write`, `unlink`, custom action)
Include `ids` with the list of target record IDs:
```json
{
    "ids": [42, 43],
    "vals": {
        "state": "confirmed"
    }
}
```

---

## 4. Code Examples

### Python (using `requests`)
```python
import requests

ODOO_URL = "https://mycompany.odoo.com"
API_KEY = "6578616d706c65206a736f6e20617069206b6579"
DB_NAME = "mycompany"

headers = {
    "Authorization": f"bearer {API_KEY}",
    "Content-Type": "application/json; charset=utf-8",
    "X-Odoo-Database": DB_NAME,
    "User-Agent": "MyIntegrationService/1.0",
}

# 1. Search and Read
payload = {
    "domain": [["state", "=", "draft"]],
    "fields": ["name", "price", "partner_id"],
    "limit": 5,
}

response = requests.post(
    f"{ODOO_URL}/json/2/estate.property/search_read",
    headers=headers,
    json=payload,
)
data = response.json()
print("Search results:", data)

# 2. Create Record
create_payload = {
    "vals_list": [
        {
            "name": "New Downtown Loft",
            "price": 350000.0,
        }
    ]
}

create_resp = requests.post(
    f"{ODOO_URL}/json/2/estate.property/create",
    headers=headers,
    json=create_payload,
)
created_ids = create_resp.json()
print("Created IDs:", created_ids)

# 3. Call Record Method
action_payload = {
    "ids": created_ids,
}
action_resp = requests.post(
    f"{ODOO_URL}/json/2/estate.property/action_confirm",
    headers=headers,
    json=action_payload,
)
print("Confirmed:", action_resp.status_code)
```

### cURL
```bash
curl -X POST "https://mycompany.odoo.com/json/2/res.partner/search_read" \
     -H "Authorization: bearer 6578616d706c65206a736f6e20617069206b6579" \
     -H "Content-Type: application/json" \
     -H "X-Odoo-Database: mycompany" \
     -d '{
       "domain": [["is_company", "=", true]],
       "fields": ["id", "name", "email"],
       "limit": 5
     }'
```

---

## 5. Security & Exposing Custom Methods

- By default, all public methods on models can be invoked via the external API if the authenticated user has adequate model permissions.
- If a Python method is intended solely for internal server-side use, mark it with **`@api.private`** or prefix its name with an underscore `_`.
