// API base URLs are public. No Supabase credentials or JWT signing secrets belong here.
const isLocalFrontend = ["localhost", "127.0.0.1"].includes(window.location.hostname);
window.COURSE_USAGE_API_URL = isLocalFrontend
  ? "http://127.0.0.1:8000"
  : "https://course-usage-service.vercel.app";
