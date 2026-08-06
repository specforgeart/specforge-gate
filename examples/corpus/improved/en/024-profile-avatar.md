# Profile avatar

## Goal
Let a user replace the image shown on the account profile.

## Expected result
The profile references the accepted image and no longer references the previous image.

## Out of scope
- Image cropping.
- Animated images.
- Public image galleries.

## Acceptance criteria
- Given a JPEG below 5 MB, when it is submitted, then the profile references the new image.
- Given a PNG below 5 MB, when it is submitted, then the profile references the new image.
- Given a 6 MB file, when it is submitted, then the request is rejected.

## Errors and edge cases
- Unsupported image types are rejected.
- An interrupted storage write preserves the previous avatar.
