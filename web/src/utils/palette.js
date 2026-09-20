// Base palette pulled from brainstorming/color_palette.jpeg
export const BASE_PALETTE = {
  deepWine: '#452928',
  burgundy: '#74362d',
  khaki: '#a49250',
  pastelBlueGrey: '#9dbcd1',
}

// Spine colors: the 4 brainstormed colors plus a few tints/shades of each
// so a shelf of books doesn't read as only 4 repeating colors, while still
// staying inside the same warm/muted family.
export const SPINE_COLORS = [
  '#452928', // deep wine
  '#74362d', // burgundy
  '#a49250', // khaki
  '#9dbcd1', // pastel blue grey
  '#8c4a3f', // burgundy, lighter
  '#5c3a1e', // warm umber
  '#6d7a4f', // muted olive
  '#c2a878', // sandy tan
  '#4f6b7a', // slate blue
  '#8a3f4a', // muted rose
]

// Deterministic hash so the same book always gets the same spine color,
// instead of a random color reshuffling on every render/navigation.
function hashString(str) {
  let hash = 0
  for (let i = 0; i < str.length; i += 1) {
    hash = (hash << 5) - hash + str.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash)
}

export function spineColorFor(id) {
  return SPINE_COLORS[hashString(String(id)) % SPINE_COLORS.length]
}

// Simple luminance check so spine text stays readable against whichever
// color the book lands on.
export function textColorFor(hexColor) {
  const hex = hexColor.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.6 ? BASE_PALETTE.deepWine : '#f3ede3'
}
