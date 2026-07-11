# Public-repository inventory query

Cutoff: `2026-07-11T21:40:00Z`

Scope:

- GitHub user `pselamy`, public repositories returned by the REST API.
- GitHub organization `selamy-labs`, public repositories returned by the REST API.

Authenticated GitHub CLI commands used for the source pages:

```sh
gh api --paginate 'users/pselamy/repos?type=public&per_page=100'
gh api --paginate 'orgs/selamy-labs/repos?type=public&per_page=100'
```

Derivations:

- `total`: length of the combined responses.
- owner counts: group by `owner.login`.
- `archived`: `archived == true`.
- `forks`: `fork == true`.
- `active_originals`: both `archived == false` and `fork == false`.
- `created_since_2026_03_01`: `created_at >= 2026-03-01T00:00:00Z`.

Archived and fork counts overlap and therefore must not be added together. “Active original” is only a compact filter name for the two API flags; it does not establish maintenance activity, originality of every line, ownership of upstream ideas, or operational value.

The committed snapshot intentionally stores aggregate counts and the non-archived non-fork identities rather than descriptions or repository contents. Re-run the paginated queries before making a current-state claim.
