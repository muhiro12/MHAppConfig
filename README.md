# MHAppConfig

Application-owned configuration for apps built on
[MHPlatform](https://github.com/muhiro12/MHPlatform).
Configuration history is independent of each app's source releases.

## Applications

| App | Configuration | Status |
| --- | --- | --- |
| Incomes | [incomes/app.json](incomes/app.json) | Awaiting MHPlatform #16 |

`app.json` records the app's identity, App Store ID, storefront, and current
minimum supported version. These are public configuration values, not credentials
or user data. The minimum version is carried forward from the app's existing
configuration; recording it here does not activate a new update requirement.

## Deployment status

No scheduled-update policy is deployed yet. `app.json` is an onboarding record,
not a document accepted by `MHRemoteUpdateController`. Do not use it as the
controller's policy URL.

MHPlatform 1.17 requires an absolute policy-document expiry with a maximum
30-day lifetime in its standard integration. The intended operation here is to
change configuration only when a policy decision changes, without a periodic
renewal job. Static-policy support is tracked in
[MHPlatform #16](https://github.com/muhiro12/MHPlatform/issues/16).

After that contract is available, publish each app's policy as
`<app>/update-policy.json` on `main`, verify its anonymous HTTPS Raw response with
the supported MHPlatform decoder, and then configure the adopting app's endpoint.
Use the branch-based Raw URL so policy changes can reach already-installed apps.

Incomes continues to use its existing
[legacy configuration](https://github.com/muhiro12/Incomes/blob/main/.config.json)
until scheduled-policy adoption is completed. Keep that file compatible with
already-distributed versions.

## Editing

- Keep app-specific files in the app's directory and retain stable deployed paths.
- Review the diff before publishing: changes to a deployed Raw file are live
  operational changes, independent of an App Store release.
- Follow MHPlatform's supported wire format and revision rules when policy
  deployment begins. Missing files and failed requests are not cancellation.

For the current Incomes record, run these checks from the repository root:

```sh
python3 -m json.tool incomes/app.json > /dev/null
git diff --check
```
