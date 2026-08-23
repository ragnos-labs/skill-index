# Review receipt instructions

Each `reviews/<skill-name>.json` records the human or agent review that allowed
a skill bundle to reach its lifecycle state.

- Review the full skill folder, including scripts, references, and assets.
- Record evidence, source references, limitations, and reviewer identity.
- `make review-bind` updates only the bundle digest. It does not perform or
  claim a review.
- Active skills require `status: reviewed` and an exact digest match.
- Experimental skills may use `status: pending` with an empty digest.
- Changing a skill invalidates the old digest until it is reviewed and rebound.
