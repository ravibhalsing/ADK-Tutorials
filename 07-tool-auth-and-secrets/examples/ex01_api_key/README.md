# Example 01 — API-key auth on an OpenAPI toolset

NASA's APOD API returns **403 without `?api_key=`**. The toolset injects the key; the
model never sees it.

```powershell
python run.py
adk run ex01_api_key
```
`.env`: `NASA_API_KEY=DEMO_KEY` (works with no signup; low rate limit — get your own free
key at api.nasa.gov for real use).

## Captured output

```
user> What's the astronomy picture of the day?
  [api call] get_astronomy_picture_of_the_day({})          # <-- no api_key in args
agent> Today's APOD is "Chasing the Moon's Shadow" — NASA's WB-57F aircraft flew off
       Iceland on Aug 12 to film a total solar eclipse from 50,000 ft.
       https://apod.nasa.gov/apod/image/2609/2026Eclipse_WB57GoPro_Totality_H264_1024.jpg

user> What about on 2020-07-04?
  [api call] get_astronomy_picture_of_the_day({'date': '2020-07-04'})
agent> "Meeting in the Mesosphere" — red sprites above thunderstorms and silvery
       noctilucent clouds. https://apod.nasa.gov/apod/image/2007/msv1000crop.jpg
```

## Takeaways

```python
auth_scheme, auth_credential = token_to_scheme_credential(
    "apikey", "query", "api_key", NASA_API_KEY)      # type, location, param name, value
OpenAPIToolset(spec_str=SPEC, spec_str_type="yaml",
               auth_scheme=auth_scheme, auth_credential=auth_credential)
```

- The key is attached to every HTTP request **after** the model decides to call the tool.
- Tool-call args in the event stream have no `api_key` — nothing sensitive reaches the model.
- For a header key: `token_to_scheme_credential("apikey", "header", "X-Api-Key", value)`.
