# Changelog

## Unreleased

## 0.1.1 - 2026-07-13

### Added

- Initial Tornado-focused Prometheus instrumentator.
- Default request count, request size, response size, and latency metrics.
- Custom sync and async instrumentation functions.
- Metrics endpoint exposure for Tornado applications.
- Handler exclusions, dynamic route instrumentation, custom registries, and multiprocess support.

### Fixed

- Do not record excluded handlers in the in-progress gauge or response-body capture.
- Record actual written bytes for chunked responses without `Content-Length`.
- Require release tags to point to commits already merged into `main`.
