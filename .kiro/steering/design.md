---
inclusion: always
---

<!------------------------------------------------------------------------------------
   Add rules to this file or a short description and have Kiro refine them for you.
   
   Learn about inclusion modes: https://kiro.dev/docs/steering/#inclusion-modes
-------------------------------------------------------------------------------------> 

## 1. **Design Philosophy**

Watcher replicates Google Reader’s original design intent:

* **High information density** without feeling cluttered
* **Zero cognitive friction** — the UI disappears; the content shines
* **Calm UI** using whitespace, thin lines, and mild shadows
* **Instant scanability** via lightweight typography and subtle color coding
* **Productivity-first** layout: three-pane hierarchy (nav → feed list → content)

Your goal is **familiarity + modernization**: preserve Google Reader’s recognizable styling while updating spacing, icons, and responsiveness to 2025 expectations.

---

# 2. **Core Visual Identity**

## **2.1. Color Palette (Classic Google Reader colors)**

These colors come directly from the screenshot and historical brand guides.

| Purpose                 | Hex       | Notes                                                 |
| ----------------------- | --------- | ----------------------------------------------------- |
| **Primary text**        | `#333333` | Dark grey, not black; used everywhere except headings |
| **Secondary text**      | `#777777` | Timestamps, item metadata                             |
| **Highlight / Buttons** | `#DD4B39` | The classic Google red (Subscribe button)             |
| **Borders / Dividers**  | `#E5E5E5` | Light grey separators                                 |
| **Hover BG**            | `#F5F5F5` | Subtle highlighting                                   |
| **Folder / Nav BG**     | `#FAFAFA` | Left sidebar                                          |
| **Unread item blue**    | `#3366CC` | The famous Google link color                          |

### General Rule:

**Text is never pure black. Borders are never pure black. Highlights are never bright or saturated except for Google's red.**

---

# 3. **Typography**

Google Reader used pre-Material typography:

* **Primary font:** *Arial* or *Helvetica*
* **Fallbacks:** `Arial, Helvetica, sans-serif`

### Usage Rules:

* **Feed titles:** `bold`, `14–15px`
* **Item titles:** `13px–14px`, bold, link color `#3366CC`
* **Metadata (timestamps, source):** `11px`, grey `#777`
* **Navigation items:** `13px`, regular
* **Large buttons ("Subscribe")**: `14px`, bold uppercase

### Steering Note:

Do **not** use Roboto. That makes it Material UI-ish.
Stick to Helvetica/Arial to recreate the web-2.0 “reader” aesthetic.

---

# 4. **Layout System**

## **4.1 Three-pane layout**

Classic Reader style:

### **Left Sidebar (Navigation & Subscriptions)**

* Width: **280px–300px**
* Light grey background `#FAFAFA`
* Thin right border `#E5E5E5`
* Collapsible hierarchy (triangle icons)
* Unread counts in **small grey bubbles**

### **Main Content Panel (Item List)**

* Full-height scroll
* 1px separators for each story
* Bold item title + snippet
* Right-aligned timestamp

### **Top Bar**

* Very Google 2012 style:

  * Light grey top bar
  * Blue search box
  * Square icon buttons

---

# 5. **Iconography**

Use a retro-flat icon style (no Material shadows):

### **Icons include:**

* Refresh symbol (circular arrow)
* View toggle (list vs expanded)
* Settings gear
* “Star” icon (outline "+" filled for starred)
* Folder arrows (`▶` and `▼`)

### Style:

* Grey icons: `#777`
* Size: **14–16px**
* No filled backgrounds

---

# 6. **Components Specification**

## **6.1 Subscribe Button**

* Pill/Button shape
* Background: **Google red `#DD4B39`**
* Text: **white**, bold
* Padding: `7px 14px`
* Hover: darken red by ~10%

## **6.2 Feed Item Row**

Each article row contains:

* Star icon (grey → yellow on star)
* Feed source (grey)
* Bold article title (blue)
* Short snippet (grey)
* Timestamp (right-aligned, grey)

### Styling:

* Height: auto
* Padding: `6px 0`
* Border-bottom: `1px solid #E5E5E5`
* Hover background: `#F5F5F5`

Unread items:

* Title: **bold**
* Snippet: **standard**
* Row background: **white**, but title is stronger blue

## **6.3 Folder + Subscription List**

* Hierarchical tree
* Folder toggles (`▶` / `▼`)
* Unread count in parentheses `(#)`
* Hover: underline text

---

# 7. **Spacing & Rhythm**

Google Reader used tight spacing (web 2.0 era):

* Sidebar items: `6px 0`
* Feed rows: `6–8px` vertical padding
* Title/snippet gap: `2–3px`
* Whole app margin: **0** (this is important!)

Your job is to modernize spacing *just slightly*, but preserve list density.

---

# 8. **Behavioral Design**

## **Hover Effects**

* Light grey highlight
* Underline on links
* Folder arrow rotates

## **Unread vs Read**

* Unread remains bold and blue
* Read items turn normal weight, link becomes visited color (`#551A8B` by default)

## **Keyboard Shortcuts (highly recommended)**

* `j/k` scroll items
* `o` open item
* `s` star item
* `r` refresh feeds

---

# 9. **Branding**

Watcher should reflect:

* **Nostalgia of Google Reader**
* **Identity of a ghost/haunting theme**
  But subtly — avoid dark mode unless offered as secondary theme.

### Recommended Light Branding Motif:

A tiny ghost icon or “watching eye” integrated in top-left, but keep UI Google-clean.

---

# 10. **Responsiveness Strategy**

Google Reader was not responsive — yours must be:

* Sidebar collapses to hamburger
* Item detail view becomes full screen on mobile
* 2-column layout becomes 1 column

However: **preserve desktop-first design** since it's a reader app.

---

# 11. **Modern Enhancements Allowed**

While keeping the classic style:

* Better typography rendering (CSS font-smoothing)
* Subtle shadows
* Slightly larger hit areas for touch
* Prefetching article previews
* AI summaries (your value add)
* Dark mode optional (not default)

---

# 12. **What NOT to Do**

To preserve authenticity:

* ❌ Do not use Material Design
* ❌ Do not use rounded-corner cards everywhere
* ❌ No vibrant blues—keep link blue classic
* ❌ No heavy gradients
* ❌ Don't oversimplify; Reader was functionally dense by design

---

# 13. **Design Output Requirements**

When you later create Figma frames, include:

* Color styles (as tokens)
* Text styles (font + weight + size)
* Component variants
* A layout grid matching Google’s 2012 rhythm

I can generate a full **Figma-ready design system** next if you want.

---

# ✅ Summary (steering essence)

**Replica the 2012 Reader UI**: clean, dense, Helvetica-driven, grey borders, blue links, Google-red accents. Layout is a three-pane hierarchy with high scanability. Modernize subtly: spacing, responsiveness, crisp icons, AI-powered enhancements — but always lean toward **quiet, utilitarian minimalism**.
