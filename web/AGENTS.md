# JARVIS Web collaboration notes

- This folder is the mobile friendly Vercel app. Run `npm test`, then `npm run dev` with `.env.local` filled from `.env.example`.
- Keep `GEMINI_API_KEY`, `JARVIS_ACCESS_CODE`, `JARVIS_BRIDGE_TOKEN`, and Redis REST credentials server side. Never use a `NEXT_PUBLIC_` prefix or embed them in client files.
- Gemini may propose only tools in `api/_lib.js`. A model response is a proposal, never proof of execution.
- Mobile actions need a separate click before `POST /api/jobs`. The Windows bridge validates names and arguments again. Do not add remote keyboard, mouse, shell or file overwrite actions without a separate design and explicit on device approval.
- Preserve Turkish UI and the dark teal/orange HUD. Keep mobile widths usable on iPhone.
- The desktop code is in `../app/` after publishing. Update packages are released through the root `update.json`; do not change it until an archive passes the previous version's updater validation.
