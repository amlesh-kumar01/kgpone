---
name: Illuminated Heritage
colors:
  surface: '#f9f9f9'
  surface-dim: '#dadada'
  surface-bright: '#f9f9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f3f3'
  surface-container: '#eeeeee'
  surface-container-high: '#e8e8e8'
  surface-container-highest: '#e2e2e2'
  on-surface: '#1a1c1c'
  on-surface-variant: '#44474e'
  inverse-surface: '#2f3131'
  inverse-on-surface: '#f1f1f1'
  outline: '#75777e'
  outline-variant: '#c4c6ce'
  surface-tint: '#4c5f80'
  primary: '#000b21'
  on-primary: '#ffffff'
  primary-container: '#0d2240'
  on-primary-container: '#778aad'
  inverse-primary: '#b4c7ed'
  secondary: '#775a19'
  on-secondary: '#ffffff'
  secondary-container: '#fed488'
  on-secondary-container: '#785a1a'
  tertiary: '#110b00'
  on-tertiary: '#ffffff'
  tertiary-container: '#29210d'
  on-tertiary-container: '#94886d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#b4c7ed'
  on-primary-fixed: '#051b39'
  on-primary-fixed-variant: '#344767'
  secondary-fixed: '#ffdea5'
  secondary-fixed-dim: '#e9c176'
  on-secondary-fixed: '#261900'
  on-secondary-fixed-variant: '#5d4201'
  tertiary-fixed: '#f0e1c2'
  tertiary-fixed-dim: '#d3c5a7'
  on-tertiary-fixed: '#221b07'
  on-tertiary-fixed-variant: '#4f462f'
  background: '#f9f9f9'
  on-background: '#1a1c1c'
  surface-variant: '#e2e2e2'
typography:
  headline-xl:
    fontFamily: Libre Caslon Text
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
  headline-lg:
    fontFamily: Libre Caslon Text
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Libre Caslon Text
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
  headline-md:
    fontFamily: Libre Caslon Text
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Manrope
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Manrope
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-sm:
    fontFamily: Hanken Grotesk
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1280px
  gutter: 24px
  margin-desktop: 64px
  margin-mobile: 20px
  stack-sm: 12px
  stack-md: 24px
  stack-lg: 48px
---

## Brand & Style

The design system is rooted in the "Illuminated Heritage" philosophy—a synthesis of ancient wisdom and modern academic excellence. It targets high-achieving students, parents, and scholars seeking an education that balances intellectual rigor with spiritual grounding.

The visual style is **Corporate / Modern** with **Minimalist** execution. It emphasizes prestige through expansive whitespace, structured information hierarchy, and high-quality iconography. The interface should feel like a digital extension of an elite institution: stable, serene, and profoundly authoritative. Key emotional drivers are "Nurturing" (through soft neutrals and safe layout) and "Illuminating" (through golden highlights and clear focal points).

## Colors

The palette is anchored by a **Deep Navy Blue**, representing depth of knowledge and institutional stability. This is contrasted by **Amber Gold**, used sparingly to draw attention to primary actions and denote "illumination" or achievement.

- **Primary (Deep Navy):** Used for typography, headers, and primary button backgrounds.
- **Secondary (Amber Gold):** Reserved for accents, icons, and state indicators (e.g., active menu items).
- **Tertiary (Cream/Champagne):** Used for soft background containers or subtle dividers to prevent the UI from feeling cold.
- **Background:** High-clarity white (#FFFFFF) is the primary canvas, with a subtle off-white (#F9F9F9) used for section distinction.

## Typography

This design system uses a dual-font strategy to balance tradition and utility. **Libre Caslon Text** provides an authoritative, literary feel for all high-level headings, reminiscent of classic academic manuscripts. 

**Manrope** serves as the primary body typeface, offering exceptional legibility and a modern, professional tone that keeps the platform accessible. For labels and metadata, **Hanken Grotesk** is used in uppercase with slight tracking to provide a clean, "architectural" clarity to the interface.

## Layout & Spacing

The layout follows a **Fixed Grid** model on desktop to maintain a sense of order and prestige, centered within a maximum width of 1280px. A 12-column system is utilized with generous 24px gutters to allow the content "room to breathe."

**Spacing Principles:**
- Use a 4px/8px baseline rhythm.
- Vertical stacks should favor larger gaps (48px+) between major sections to emphasize a calm, unhurried user experience.
- On mobile, the grid collapses to a single column with 20px side margins, maintaining the same 8px-based vertical rhythm.

## Elevation & Depth

To maintain a prestigious and clean look, this design system avoids heavy shadows. Instead, it utilizes **Tonal Layers** and **Low-Contrast Outlines**.

- **Surfaces:** Secondary content is placed on light-tinted backgrounds (Tertiary color) rather than being elevated by shadows.
- **Borders:** Cards and containers use thin, 1px borders in a soft gold or light gray (#E0E0E0) to define boundaries without adding visual weight.
- **Depth:** Occasional soft "Ambient Shadows" (0px 4px 20px rgba(13, 34, 64, 0.05)) are used only for high-interaction floating elements like dropdown menus or modals to provide a gentle lift.

## Shapes

The shape language is **Soft**. It avoids the clinical feel of sharp corners while steering clear of the overly casual look of high-radius pills. 

- **Buttons & Inputs:** Use a 4px (0.25rem) radius to convey precision and structure.
- **Cards & Featured Sections:** Use a 8px (0.5rem) radius to feel more welcoming and approachable.
- **Imagery:** Photography should either be sharp-edged for a "framed" gallery look or use the 8px radius.

## Components

- **Buttons:** Primary buttons are Navy Blue with white text, using the 4px radius. Secondary buttons use a Gold outline with Navy text. Ghost buttons are reserved for tertiary actions.
- **Cards:** White background with a 1px border (#E8D9BA) and an 8px corner radius. No shadow is applied in the default state; a very soft shadow may appear on hover.
- **Input Fields:** Minimalist design with a 1px bottom border or a full 1px light gray outline. Labels use Hanken Grotesk in uppercase above the field.
- **Chips/Badges:** Small, subtle backgrounds using the Tertiary color with high-contrast Navy text for categorization.
- **Icons:** Use thin-stroke, linear icons in Navy Blue. Important decorative icons (like the Lotus or Swan motifs) can be rendered in Gold.
- **Specialty Component - "The Illumination Bar":** A thin gold accent line used at the top of hero sections or cards to signify premium content.