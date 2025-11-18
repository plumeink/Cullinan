# Review Payloads — per-module Issue bodies

This file contains ready-to-paste GitHub Issue titles and bodies for each module owner to review API cleanup candidates and docs. Each section includes a short summary, the CSV rows for that module, and a checklist for the reviewer.

---

## Module: cullinan.core
**Owner:** @core-eng

Issue title (paste as issue title):
```
[Review] cullinan.core docs & API candidates
```

Issue body (paste as issue description):

```
Please review the `cullinan.core` documentation and the API cleanup candidates below.

Files to review:
- docs/modules/core.md
- docs/zh/modules/core.md
- docs/work/api_cleanup_candidates.csv (filter: module == cullinan.core)

Candidates (module,name,kind,signature,decision):
- cullinan.core,Inject,class,Inject(name: Optional[str] = None, required: bool = True),keep
- cullinan.core,InjectByName,class,InjectByName(service_name: Optional[str] = None, required: bool = True),keep
- cullinan.core,InjectionRegistry,class,InjectionRegistry(),keep
- cullinan.core,ProviderRegistry,class,ProviderRegistry(),keep
- cullinan.core,RequestScope,class,RequestScope(storage_key: str = '_scoped_instances'),keep
- cullinan.core,SingletonScope,class,SingletonScope(),keep
- cullinan.core,TransientScope,class,TransientScope(),keep
- cullinan.core,create_context,function,create_context() -> cullinan.core.context.RequestContext,keep
- cullinan.core,destroy_context,function,destroy_context() -> None,keep
- cullinan.core,get_context_value,function,get_context_value(key: str, default: Any = None) -> Any,keep
- cullinan.core,get_current_context,function,get_current_context() -> Optional[cullinan.core.context.RequestContext],keep
- cullinan.core,get_injection_registry,function,get_injection_registry() -> cullinan.core.injection.InjectionRegistry,keep
- cullinan.core,get_request_scope,function,get_request_scope() -> cullinan.core.scope.RequestScope,keep
- cullinan.core,get_singleton_scope,function,get_singleton_scope() -> cullinan.core.scope.SingletonScope,keep
- cullinan.core,get_transient_scope,function,get_transient_scope() -> cullinan.core.scope.TransientScope,keep
- cullinan.core,inject_constructor,function,inject_constructor(cls: Optional[Type] = None),keep
- cullinan.core,injectable,function,injectable(cls: Optional[Type] = None),keep
- cullinan.core,reset_injection_registry,function,reset_injection_registry() -> None,keep
- cullinan.core,set_context_value,function,set_context_value(key: str, value: Any) -> None,keep
- cullinan.core,set_current_context,function,set_current_context(context: Optional[cullinan.core.context.RequestContext]) -> None,keep

Checklist for reviewer:
- [ ] Run local smoke checks for core examples (see `docs/modules/core.md`) using the repo venv.
- [ ] For each CSV row above, update `decision` to `keep`/`remove`/`review` with a short rationale.
- [ ] Confirm examples show correct behavior for RequestScope and InjectionRegistry.
- [ ] Comment in this issue when done with a summary and any proposed doc changes.

Local smoke-check commands (PowerShell):
```
py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -U pip; pip install -e .
# Run examples or tests that exercise core, e.g.:
python -m pytest tests/test_core_injection.py -q
```
```

---

## Module: cullinan.controller
**Owner:** @controller-eng

Issue title:
```
[Review] cullinan.controller docs & API candidates
```

Issue body:

```
Please review the `cullinan.controller` documentation and the API cleanup candidates below.

Files to review:
- docs/modules/controller.md
- docs/zh/modules/controller.md
- docs/work/api_cleanup_candidates.csv (filter: module == cullinan.controller)

Candidates (module,name,kind,signature,decision):
- cullinan.controller,controller,function,controller(**kwargs) -> Callable,keep
- cullinan.controller,get_controller_registry,function,get_controller_registry() -> cullinan.controller.registry.ControllerRegistry,keep
- cullinan.controller,get_header_registry,function,get_header_registry() -> cullinan.controller.core.HeaderRegistry,keep
- cullinan.controller,request_resolver,function,request_resolver(self, url_param_key_list: Optional[Sequence] = None, url_param_value_list: Optional[Sequence] = None, query_param_names: Optional[Sequence] = None, body_param_names: Optional[Sequence] = None, file_param_key_list: Optional[Sequence] = None) -> Tuple[Optional[dict], Optional[dict], Optional[dict], Optional[dict]],keep
- cullinan.controller,reset_controller_registry,function,reset_controller_registry() -> None,keep
- cullinan.controller,response_build,function,response_build(**kwargs) -> cullinan.controller.core.StatusResponse,keep

Checklist for reviewer:
- [ ] Verify controller decorator signatures and example usage in `docs/modules/controller.md`.
- [ ] Update CSV decisions where necessary and add rationale.
- [ ] Run controller-related tests or examples.

Local smoke-check:
```
py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -U pip; pip install -e .
python examples\controller_di_middleware.py
```
```

---

## Module: cullinan.service
**Owner:** @service-eng

Issue title:
```
[Review] cullinan.service docs & API candidates
```

Issue body:

```
Please review the `cullinan.service` documentation and the API cleanup candidates below.

Files to review:
- docs/modules/service.md
- docs/zh/modules/service.md
- docs/work/api_cleanup_candidates.csv (filter: module == cullinan.service)

Candidates (module,name,kind,signature,decision):
- cullinan.service,Service,class,Service(),keep
- cullinan.service,ServiceRegistry,class,ServiceRegistry(),keep
- cullinan.service,get_service_registry,function,get_service_registry() -> cullinan.service.registry.ServiceRegistry,keep
- cullinan.service,reset_service_registry,function,reset_service_registry() -> None,keep
- cullinan.service,service,function,service(cls: Optional[Type[cullinan.service.base.Service]] = None, *, dependencies: Optional[List[str]] = None),keep

Checklist for reviewer:
- [ ] Validate service lifecycle notes in `docs/modules/service.md` and its example.
- [ ] Update CSV decisions and rationale as appropriate.
- [ ] Run `tests/test_provider_system.py` locally.

Local smoke-check:
```
py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -U pip; pip install -e .
python -m pytest tests/test_provider_system.py -q
```
```

---

## Module: cullinan.app / cullinan.application
**Owner:** @writer/dev

Issue title:
```
[Review] cullinan.app & cullinan.application docs
```

Issue body:

```
Please review the `cullinan.app` and `cullinan.application` documentation and confirm startup/shutdown examples.

Files to review:
- docs/modules/app.md
- docs/modules/application.md
- docs/zh/modules/app.md
- docs/zh/modules/application.md
- docs/work/api_cleanup_candidates.csv (filter: module in [cullinan.app, cullinan.application])

Candidates (module,name,kind,signature,decision):
- cullinan.application,run,function,run(handlers=None),keep
- cullinan.app,CullinanApplication,class,CullinanApplication(shutdown_timeout: int = 30),keep
- cullinan.app,create_app,function,create_app(shutdown_timeout: int = 30) -> cullinan.app.CullinanApplication,keep

Checklist for reviewer:
- [ ] Verify startup sequence steps and sample code in `docs/getting_started.md` and `docs/modules/application.md`.
- [ ] Update CSV decisions if needed.
- [ ] Run `tests/test_real_app_startup.py` locally to validate behavior.

Local smoke-check:
```
py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -U pip; pip install -e .
python -m pytest tests/test_real_app_startup.py -q
```
```

---

### How to use these payloads
- Copy the corresponding Issue title and body into a new GitHub Issue and assign the module owner.
- Ask the owner to update `docs/work/api_cleanup_candidates.csv` decisions and comment in the issue with the commit hash that updated the CSV.


