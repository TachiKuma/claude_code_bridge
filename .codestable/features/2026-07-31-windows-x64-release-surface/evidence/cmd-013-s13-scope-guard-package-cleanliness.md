# CMD-013 S13 scope guard and package cleanliness

## 结果

- `python -m pytest -q test/test_windows_x64_release_surface.py test/test_cli_doctor_windows_x64_release_surface.py test/test_windows_bootstrap_script.py test/test_cli_management_update.py -k "windows or release_surface or install or update or doctor"`: 85 passed
- `python -m pytest -q test/test_cli_doctor_rmux_packaging.py test/test_install_windows_rmux_contract.py test/test_rmux_packaging_docs_contracts.py`: 5 passed
- `npm pack --dry-run --json` via platform-safe wrapper: projection JSON present in payload
- scope guard: no publish/push/tag/support/completion hits

## 备注

- 本轮只收口发布面边界，不扩展到 publish/promotion/support 宣称。
