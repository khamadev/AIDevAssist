const COVER_GRADIENTS = [
  ["#0f766e", "#14b8a6"],
  ["#7c3aed", "#a78bfa"],
  ["#b45309", "#f59e0b"],
  ["#be123c", "#fb7185"],
  ["#1d4ed8", "#60a5fa"],
  ["#166534", "#4ade80"],
];

function destinationCover(destination) {
  let hash = 0;
  for (let i = 0; i < destination.length; i++) {
    hash = destination.charCodeAt(i) + ((hash << 5) - hash);
  }
  const [from, to] = COVER_GRADIENTS[Math.abs(hash) % COVER_GRADIENTS.length];
  return `linear-gradient(135deg, ${from}, ${to})`;
}

function tripStatus(startDate, endDate) {
  const today = new Date().toISOString().slice(0, 10);
  if (today < startDate) return "upcoming";
  if (today > endDate) return "past";
  return "ongoing";
}

function tripStatusLabel(status) {
  return { upcoming: "Upcoming", ongoing: "In progress", past: "Past" }[status];
}

function tripDurationDays(startDate, endDate) {
  const start = new Date(startDate);
  const end = new Date(endDate);
  return Math.round((end - start) / (1000 * 60 * 60 * 24)) + 1;
}

function daysUntil(startDate) {
  const today = new Date().toISOString().slice(0, 10);
  const diff = Math.round((new Date(startDate) - new Date(today)) / (1000 * 60 * 60 * 24));
  return diff;
}

function formatDateRange(startDate, endDate) {
  const opts = { month: "short", day: "numeric" };
  const start = new Date(startDate).toLocaleDateString(undefined, opts);
  const end = new Date(endDate).toLocaleDateString(undefined, opts);
  return `${start} - ${end}`;
}
