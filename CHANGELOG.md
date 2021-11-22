# Changelog

## [0.9.6] - 2021-11-21

### Fixed

- Exception method fix.

## [0.9.5] - 2021-11-21

### Fixed

- Bug fixes with empty strings while processing tweets.

## [0.9.4] - 2021-11-13

### Changed

- Upgraded tweepy, pymongo.

### Fixed

- API call fixes.

## [0.9.3] - 2020-08-29

### Added

- `exclude_users`: list of users whose tweets will be excluded corresponding to a given hash tag 
- A tweet which is a reply will be excluded from being retweeted

### Fixed

- `include_strs` is now considered if exists for a given hash tag

## [0.9.2] - 2020-08-01

### Added

- `hash_tags_meta`: extra details to decide inclusion and exclusion of tweets
- `CHANGELOG.md` file to keep track of changes across different tags/releases

### Changed

- [README] and [documentation] are updated with new `hash_tags_meta` details

[0.9.6]: https://github.com/acrlakshman/twitter-bot-computational-fluids/compare/v0.9.5...v0.9.6
[0.9.5]: https://github.com/acrlakshman/twitter-bot-computational-fluids/compare/v0.9.4...v0.9.5
[0.9.4]: https://github.com/acrlakshman/twitter-bot-computational-fluids/compare/v0.9.3...v0.9.4
[0.9.3]: https://github.com/acrlakshman/twitter-bot-computational-fluids/compare/v0.9.2...v0.9.3
[0.9.2]: https://github.com/acrlakshman/twitter-bot-computational-fluids/compare/v0.9.1...v0.9.2
[documentation]: https://acrlakshman.github.io/twitter-bot-computational-fluids/
[README]: https://github.com/acrlakshman/twitter-bot-computational-fluids/blob/master/README.md
