# Design System Specification: The Academic Architect

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Academic Architect."** 

We are moving away from the "generic SaaS" look toward a high-precision, editorial experience that feels like a bespoke digital laboratory. This aesthetic—**Milled Intelligence**—treats the interface as a physical object carved from high-grade materials. We achieve this through "mathematical" layouts: intentional asymmetry, high-contrast typography scales, and a rejection of standard grid containers in favor of layered, tonal depth.

The goal is to feel **authoritative yet approachable**. We use the vibrancy of the primary and accent colors to denote intelligence and action, while the vast white space provides the "breathing room" required for deep learning and focus.

---

## 2. Colors & Surface Philosophy
This system uses a sophisticated palette of off-whites and vibrant functional colors to guide the eye without overwhelming the user’s cognitive load.

### Surface Hierarchy & Nesting
Instead of using lines to separate sections, we use **Tonal Layering**. Think of the UI as stacked sheets of fine paper.
*   **Base Layer:** Use `surface` (#f8f9fa) for the main canvas.
*   **Functional Layer:** Use `surface-container-low` (#f3f4f5) for sidebars or secondary navigation.
*   **Action Layer:** Use `surface-container-lowest` (#ffffff) for primary content cards or "milled" surfaces that need to pop.

### The "No-Line" Rule
**Prohibit the use of 1px solid borders for sectioning.** Large layout blocks must be defined solely by color shifts (e.g., a `surface-container-high` header sitting on a `surface` body). 

### The "Glass & Gradient" Rule
To add "soul" to the AI-forward experience:
*   **Signature Textures:** Use subtle linear gradients for primary CTAs, transitioning from `primary` (#0058bc) to `primary_container` (#0070eb) at a 135-degree angle.
*   **Glassmorphism:** Use `surface-container-lowest` with 80% opacity and a `20px` backdrop-blur for floating navigation bars or modal overlays. This ensures the "Academic" feel doesn't become "Static."

---

## 3. Typography: Precision Inter
We use **Inter** exclusively to lean into its technical, high-precision DNA.

*   **Display & Headlines:** Use `display-lg` to `headline-sm` for editorial moments. These should feel authoritative. Use `tight` letter-spacing (-0.02em) to give it a "milled" look.
*   **Body & Labels:** Use `body-md` for high readability. Labels (`label-md`) should be uppercase with `+0.05em` tracking to mimic the look of architectural blueprints.
*   **Hierarchy:** The brand identity is conveyed through the massive scale difference between Headlines and Body. Don't be afraid to use `display-md` for a page title next to `body-sm` metadata—this "Editorial Tension" creates a premium feel.

---

## 4. Elevation & Depth
Depth in this design system is achieved through physics, not just aesthetics.

*   **The Layering Principle:** Place a `surface-container-lowest` (#ffffff) card on a `surface-container-low` (#f3f4f5) background. This creates a "soft lift" that feels architectural rather than digital.
*   **Ambient Shadows:** For floating elements (Modals, Popovers), use extra-diffused shadows.
    *   *Shadow Color:* A tinted version of `on-surface` at 4% opacity.
    *   *Blur:* 32px to 64px.
*   **The "Ghost Border" Fallback:** If a container requires a border for accessibility, use a **Ghost Border**: `outline-variant` (#c1c6d7) at **20% opacity**. Never use a 100% opaque border for containment.

---

## 5. Components

### Buttons
*   **Primary:** Linear gradient (`primary` to `primary_container`). `0.375rem` (md) corner radius. High-precision 1px "Ghost Border" in a lighter shade of blue to mimic a beveled edge.
*   **Tertiary:** No background. Use `primary` text. Upon hover, shift the background to `surface-container-high`.

### Input Fields
*   **Styling:** `surface-container-lowest` background with a 1px "Ghost Border." 
*   **States:** On focus, the border transitions to `primary` (#0058bc) but remains 1px. Precision over thickness.

### Chips (Learning Tags)
*   Use `secondary_container` (#86f898) for "Success" or "Completed" states.
*   Use `tertiary_container` (#d9372b) for "Critical" or "Urgent" states.
*   All chips use `label-md` for text, centered with generous horizontal padding.

### Cards & Lists
*   **Forbid Dividers:** Do not use horizontal lines to separate list items. Use 16px or 24px of vertical whitespace.
*   **Hover States:** When hovering over a list item or card, change the background to `surface-container-highest` or add a subtle `4%` ambient shadow.

### AI-Forward Elements (The "Pulse")
*   For AI-generated content or paths, use a subtle "Pulse" border: a 1px `Ghost Border` that uses a gradient of `primary` (#0058bc) to `secondary` (#006e2c).

---

## 6. Do's and Don'ts

### Do:
*   **Do** use asymmetrical layouts. Place text on the left and leave the right 40% of the screen as white space for a "Gallery" feel.
*   **Do** use the Roundedness Scale (`0.25rem` for small, `0.75rem` for large) consistently to maintain the "Milled" look.
*   **Do** ensure all text meets AA accessibility standards against the `surface` colors.

### Don't:
*   **Don't** use pure black (#000000). Use `on-surface` (#191c1d) for all "black" text to keep the look soft and premium.
*   **Don't** use standard "drop shadows" with high opacity. If it looks like a shadow, it’s too dark. It should look like "ambient light."
*   **Don't** use dividers for layout sectioning. If you need a break, use a `surface-container` color shift.