# MHAppConfig

Application-owned configuration for apps built on
[MHPlatform](https://github.com/muhiro12/MHPlatform).
Configuration history is independent of each app's source releases.

## Applications

| App | Shared configuration |
| --- | --- |
| Incomes | [incomes/app.json](incomes/app.json) |

The shared configuration envelope contains `schemaVersion`, `bundleIdentifier`,
and `features`. Each feature owns its policy and revisions. Incomes currently
uses only `features.remoteUpdate`; additional feature sections can share the
same document when an adopting app needs them.

Incomes uses App Store ID `1584472982` and explicitly selects the `jp`
publication reference in its app-side controller. Those values configure the
client and are not remotely changed by this document.

## Publishing

The live Incomes configuration is available without authentication at this
[HTTPS Raw URL](https://raw.githubusercontent.com/muhiro12/MHAppConfig/main/incomes/app.json).
Clients use the branch-based URL so operational changes can reach installed
apps independently of an App Store release. Keep deployed paths stable.

This document uses the static configuration contract introduced in MHPlatform
1.18.0. An unchanged policy needs no publisher renewal, expiry timestamp,
scheduled workflow, or periodic commit. Successful validated network fetches
renew bounded client-side evidence; local cache reads and failed requests do not.

The app retains its existing minimum supported version in the initial update
policy. The app's source repository keeps the
[legacy configuration](https://github.com/muhiro12/Incomes/blob/main/.config.json)
for already-distributed clients; it has a different format and endpoint.

## Editing update policy

- Edit `features.remoteUpdate` only when the update decision changes.
- Increase its positive `revision` for every change, including postponement and
  cancellation. An existing revision is immutable and must not be rolled back.
- Set `requirement.minimumVersion` and an absolute UTC `effectiveAt` when an
  update should become required. An optional `endsAt` ends that requirement.
- Cancel with a higher revision and an explicit `requirement: null`. Missing
  fields, deleted files, invalid JSON, and failed requests are not cancellation.
- Do not add `issuedAt` or `validUntil`; those publisher-authored expiry fields
  are rejected by this contract.
- Review the exact diff before publishing. A push to `main` changes the live
  configuration. Reverting a policy requires another higher revision, rather
  than republishing an older file.

Read the package's
[configuration and update contract](https://github.com/muhiro12/MHPlatform/blob/1.18.0/Designs/Architecture/remote-update.md)
for feature isolation, offline freshness, and App Store publication checks.
Only public configuration belongs here; credentials and user data do not.

From the repository root, check JSON syntax and whitespace before committing:

```sh
python3 -m json.tool incomes/app.json > /dev/null
git diff --check
```

Syntax checks do not validate policy semantics. Before changing the wire format
or enabling a new consumer, also verify the exact file with the supported
MHPlatform decoder and the adopting app's relevant tests and runtime checks.
