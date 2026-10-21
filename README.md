# MHAppConfig

Application-owned configuration for apps built on
[MHPlatform](https://github.com/muhiro12/MHPlatform).
Configuration history is independent of each app's source releases.

## Applications

| App | Shared configuration |
| --- | --- |
| Incomes | [incomes/app.json](incomes/app.json) |
| Cookle | [cookle/app.json](cookle/app.json) |
| Stally | [stally/app.json](stally/app.json) |

The shared configuration envelope contains `schemaVersion`, `bundleIdentifier`,
and `features`. The update feature has its own `schemaVersion` (currently 1;
omission also means 1), independently of the envelope version and policy
revision. Each feature owns its policy and revisions. Incomes currently
uses only `features.remoteUpdate`; additional feature sections can share the
same document when an adopting app needs them.

Incomes uses App Store ID `1584472982` and the package's default publication
reference without a fixed country code. Store identity belongs to the client
and is not remotely changed by this document.

Cookle uses App Store ID
`6483363226` and confirms publication in the Japanese storefront. Its initial
revision has no active minimum or scheduled requirement. Missing or expired
evidence keeps offline editing available; a confirmed required update blocks
library data mutations from both the app and shortcuts. Reading and exporting
remain available.

Stally uses App Store ID `6760996986`; its initial revision has no active
minimum or scheduled requirement while its first public release is being
prepared.

## Publishing

The live Incomes configuration is available without authentication at this
[HTTPS Raw URL](https://raw.githubusercontent.com/muhiro12/MHAppConfig/main/incomes/app.json).
Cookle reads [its own HTTPS Raw URL](https://raw.githubusercontent.com/muhiro12/MHAppConfig/main/cookle/app.json).
Stally reads [its own HTTPS Raw URL](https://raw.githubusercontent.com/muhiro12/MHAppConfig/main/stally/app.json).
Clients use the branch-based URL so operational changes can reach installed
apps independently of an App Store release. Keep deployed paths stable.

Adopting apps use MHPlatform 1.20.0 or later, including its timed update plans
and automatic isolation of update-section failures. An unchanged policy needs
no publisher renewal, expiry timestamp, scheduled workflow, or periodic commit.
Successful validated network fetches renew bounded client-side evidence;
local cache reads and failed requests do not.

Incomes retains its existing minimum supported version in the initial update
policy, with an empty `scheduledRequirements` list. No future Incomes update
is scheduled. The app's source repository keeps the
[legacy configuration](https://github.com/muhiro12/Incomes/blob/main/.config.json)
for already-distributed clients; it has a different format and endpoint.

## Editing update policy

- Edit `features.remoteUpdate` only when the update decision changes.
- Increase its positive `revision` for every change, including postponement and
  cancellation. An existing revision is immutable and must not be rolled back.
- Keep the current baseline in `requirement`. Add future requirements to
  `scheduledRequirements` without replacing that baseline. Each requirement
  has `minimumVersion`, an absolute UTC `effectiveAt`, and optional `endsAt`.
- The highest currently active minimum applies, regardless of array order.
  Ended or removed plans leave other active requirements in force. Each
  revision replaces the complete baseline and plan list.
- Cancel all requirements with a higher revision, explicit `requirement: null`,
  and `scheduledRequirements: []`. To cancel only plans, clear the list while
  retaining the baseline. Missing fields, deleted files, invalid JSON, and
  failed requests are not cancellation.
- Do not add `issuedAt` or `validUntil`; those publisher-authored expiry fields
  are rejected by this contract.
- Review the exact diff before publishing. A push to `main` changes the live
  configuration. Reverting a policy requires another higher revision, rather
  than republishing an older file.

Read the package's
[configuration and update contract](https://github.com/muhiro12/MHPlatform/blob/1.20.0/Designs/Architecture/remote-update.md)
for feature isolation, plan evaluation, offline freshness, and App Store
publication checks. Maintain one current shared configuration per app, without
separate policy endpoints for obsolete prerelease readers.
Only public configuration belongs here; credentials and user data do not.

## Validation before publication

The repository pins the package's validator source in `.mhplatform-revision`.
On macOS with Xcode installed, run:

```sh
bash scripts/validate.sh
git diff --check
```

The first command obtains the pinned public MHPlatform source and builds only
its configuration/update modules with Apple's compiler. It adds no app-side
configuration or dependency. An existing clean checkout at the pinned revision
can be used offline with `MHPLATFORM_CHECKOUT=/path/to/MHPlatform`.
The generated checkout, modules, and executable remain in ignored `.build/`.

The validator uses the same decoder and immutable-revision comparison as the
package's runtime. It checks every `*/app.json` and compares it with readable
policy in the destination branch's first-parent history. It rejects invalid
requirements, unsupported format versions, identity changes, endpoint deletion,
lower revisions, and changed content at an already published revision. Sibling
features do not change update-policy revisions. It does not check App Store
publication or make a live update happen.

Enable the repository-local sending check once per clone:

```sh
git config --local core.hooksPath .githooks
```

The hook validates the exact commits being sent to `main`; uncommitted repairs
do not clear a broken outgoing commit. It also refuses deletion and rewriting
of the live branch. Other development branches are unaffected. The PR workflow
runs the same checks and recovery tests with read-only permissions.
A push-triggered run is a diagnostic after publication, not a publication gate.
Local hooks can be bypassed by other clients. To enforce the check on GitHub,
require the PR job and updates through pull requests in branch rules. Those
server-side rules and the deployment URL are not changed by this tooling.

## Recovery and rollout

Repair a bad policy with a revision greater than **every previously published
revision**, preserving the intended baseline and complete plan list. Do not
restore an old Git revision, delete the endpoint, or reuse a revision. An
unreadable historical file is reported and skipped for this contract's revision
comparison; the candidate is still checked against all readable policies in the
retained main-branch history. This does not establish compatibility with older
reader formats. This allows repair of malformed JSON without bypassing known
revision history. Shallow repositories are rejected because they can hide a
previously published revision. Keep complete Git history for validation and
preserve deployed paths.

If a client already cached valid policy, removing or corrupting the remote file
cannot cancel it. Publish an explicit higher-revision cancellation. Offline
clients observe it on a later successful fetch; local and publication evidence
retain their normal bounded lifetime. This is not an immediate global revocation
or a replacement for server-side authorization.

The original app-owned legacy endpoint must remain available until its deployed
readers are retired. Introducing this shared endpoint cannot redirect an older
binary retroactively. Do not enable a new policy format on the same URL until
all readers using that URL understand its compatibility rules; use a new
endpoint for an incompatible future reader migration.

Publish the pinned MHPlatform revision **before** sending these validator files
to MHAppConfig, so clean clones and PR jobs can obtain it. Updating this tooling
does not change the current Incomes policy or begin app adoption. App-specific
integration and Store release still require their own tests and rollout.
