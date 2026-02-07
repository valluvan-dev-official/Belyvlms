from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from urllib.parse import quote

def home(request):
    return render(request, 'home.html')

def custom_404(request, exception):
    return render(request, '404.html', status=404)


def public_register(request):
    token = request.GET.get("token", "")
    frontend_base_url = (getattr(settings, "FRONTEND_BASE_URL", "") or "").strip()
    if frontend_base_url:
        frontend_base_url = frontend_base_url.rstrip("/")
        if token:
            return HttpResponseRedirect(f"{frontend_base_url}/public/register?token={quote(token, safe='')}")
        return HttpResponseRedirect(f"{frontend_base_url}/public/register")

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>BelyvLMS Registration</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .row {{ margin-bottom: 12px; }}
    input, textarea {{ width: 100%; padding: 8px; }}
    button {{ padding: 10px 14px; }}
    pre {{ background: #f6f8fa; padding: 12px; overflow: auto; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
  </style>
</head>
<body>
  <h2>Registration</h2>
  <div class="row">
    <div><b>Token</b></div>
    <input id="token" value="{token}" />
  </div>
  <div class="row">
    <button id="load">Load Form Schema</button>
  </div>
  <div class="row">
    <div><b>Schema</b></div>
    <pre id="schema">Click "Load Form Schema"</pre>
  </div>
  <h3>Submit</h3>
  <div class="grid">
    <div class="row">
      <div><b>First name</b></div>
      <input id="first_name" />
    </div>
    <div class="row">
      <div><b>Last name</b></div>
      <input id="last_name" />
    </div>
  </div>
  <div class="row">
    <div><b>Profile JSON</b> (example: {{ "mode_of_class": "ON", "week_type": "WD" }})</div>
    <textarea id="profile" rows="10">{{}}</textarea>
  </div>
  <div class="row">
    <button id="submit">Submit Registration</button>
  </div>
  <div class="row">
    <div><b>Response</b></div>
    <pre id="resp"></pre>
  </div>
  <script>
    const schemaEl = document.getElementById('schema');
    const respEl = document.getElementById('resp');
    const tokenEl = document.getElementById('token');
    const loadBtn = document.getElementById('load');
    const submitBtn = document.getElementById('submit');
    const firstNameEl = document.getElementById('first_name');
    const lastNameEl = document.getElementById('last_name');
    const profileEl = document.getElementById('profile');

    loadBtn.addEventListener('click', async () => {{
      respEl.textContent = '';
      const token = tokenEl.value.trim();
      if (!token) {{
        schemaEl.textContent = 'Token missing';
        return;
      }}
      const res = await fetch(`/api/rbac/public/onboard/schema/?token=${{encodeURIComponent(token)}}`);
      const data = await res.json();
      schemaEl.textContent = JSON.stringify(data, null, 2);
    }});

    submitBtn.addEventListener('click', async () => {{
      respEl.textContent = '';
      const token = tokenEl.value.trim();
      if (!token) {{
        respEl.textContent = 'Token missing';
        return;
      }}
      let profile = {{}};
      try {{
        profile = JSON.parse(profileEl.value || '{{}}');
      }} catch (e) {{
        respEl.textContent = 'Profile JSON invalid';
        return;
      }}
      const payload = {{
        first_name: firstNameEl.value.trim(),
        last_name: lastNameEl.value.trim(),
        profile
      }};
      const res = await fetch(`/api/rbac/public/onboard/submit/?token=${{encodeURIComponent(token)}}`, {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(payload)
      }});
      const data = await res.json();
      respEl.textContent = JSON.stringify(data, null, 2);
    }});
  </script>
</body>
</html>"""
    return HttpResponse(html)
