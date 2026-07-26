# خطة تحسين تصميم واجهة Sticker Video Generator
**مستوحاة من أسلوب Flowstate — Immersive Dark Hero**

---

## الوضع الحالي

الواجهة الحالية تعمل وظيفياً بشكل كامل لكنها بسيطة التصميم:
- خلفية مسطحة `#050508`
- كروت المشاهد بتدرج خطي بسيط
- أزرار بتدرج `cyan → violet`
- لا توجد حركات دخول (entrance animations)
- لا يوجد عمق بصري (glassmorphism / layers)

---

## الرؤية الجديدة

واجهة **غامرة (Immersive)** بأسلوب "Dark Hero" تجمع بين:
- **خلفية WebGL متحركة** (fluid ink simulation) خلف المحتوى
- **Glassmorphism** في كل العناصر التفاعلية
- **Staggered reveal** — ظهور متتابع أنيق عند تحميل الصفحة
- **Typography احترافية** بخط Onest (أو الإبقاء على Cairo للعربية)

---

## 1. نظام الألوان (Color Tokens)

```css
:root {
  --base:              #04050c;     /* خلفية عميقة */
  --heading:           #eef0f6;     /* عناوين ساطعة */
  --body-muted:        #b9becf;     /* نص ثانوي */
  --accent-cyan:       #00E5FF;     /* اللون المميز الأساسي */
  --accent-violet:     #7C4DFF;     /* اللون المميز الثانوي */
  --glass-fill:        rgba(255,255,255,0.06);
  --glass-border:      rgba(255,255,255,0.12);
  --glass-fill-hover:  rgba(255,255,255,0.10);
  --scrim:             rgba(4,5,12,0.46);
  --scrim-strong:      rgba(4,5,12,0.68);
  --success:           #4CAF50;
  --error:             #ff5252;
  --duration-fast:     150ms;
  --ease-entrance:     cubic-bezier(0.2, 0, 0, 1);
}
```

---

## 2. الخطوط (Typography)

| الدور | الخط | الحجم | الوزن |
|-------|------|-------|-------|
| العنوان الرئيسي | Cairo | 32px (mobile) / 42px (desktop) | 900 |
| النص الثانوي | Cairo | 15px | 400 |
| الأزرار والبادج | Cairo | 14-16px | 700 |
| الحقول | Cairo | 14-15px | 400 |

---

## 3. هيكل الصفحة (Layout Overhaul)

```
┌──────────────────────────────────────────────┐
│  [Canvas: WebGL Fluid Ink — z:0]             │
│  [Scrim Overlay — z:1]                       │
│                                              │
│  ┌──── Header Nav (z:20) ────────────────┐   │
│  │  🌊 Sticker Video    [Get Started]    │   │
│  └───────────────────────────────────────┘   │
│                                              │
│  ┌──── Center Column (z:10) ────────────┐    │
│  │  ┌─ Glass Badge ─┐                   │    │
│  │  │ 🎬 Video Gen  │                   │    │
│  │  └───────────────┘                    │    │
│  │                                       │    │
│  │  ┌─ Scene Card (Glass) ─────────────┐ │    │
│  │  │  Scene 1                         │ │    │
│  │  │  [Image Upload Zone]             │ │    │
│  │  │  [Text Area]                     │ │    │
│  │  └─────────────────────────────────┘ │    │
│  │                                       │    │
│  │  [+ Add] [- Remove]                  │    │
│  │                                       │    │
│  │  ┌─ Glass Generate Bar ────────────┐  │    │
│  │  │  [▶ Generate Video]             │  │    │
│  │  └────────────────────────────────┘  │    │
│  │                                       │    │
│  │  ┌─ Progress (Glass) ──────────────┐  │    │
│  │  │  ████████░░░  67%               │  │    │
│  │  └────────────────────────────────┘  │    │
│  │                                       │    │
│  │  ┌─ Result Video ──────────────────┐  │    │
│  │  │  [Video Player]                 │  │    │
│  │  │  [⬇ Download]                   │  │    │
│  │  └────────────────────────────────┘  │    │
│  └───────────────────────────────────────┘    │
│                                              │
│  ┌──── Footer (z:20) ────────────────────┐   │
│  │  © 2026 Sticker Video Generator       │   │
│  └───────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

---

## 4. المكونات المرئية الجديدة

### 4.1 خلفية WebGL Fluid (اختياري — حسب الوقت)
- محاكاة حبر سائل (ink-in-water) بألوان `cyan → blue → violet`
- Canvas مطلق الموقع خلف كل المحتوى (`z-index: 0`)
- Scrim تدريجي شعاعي فوقه لضمان قراءة النص
- **بديل سريع إذا ضاق الوقت:** تدرج شعاعي متحرك CSS-only:
  ```css
  background: radial-gradient(ellipse at 30% 50%, #0a1628 0%, #04050c 70%);
  ```

### 4.2 Glassmorphism لكل العناصر
كل كارت مشهد، زر، وشريط تقدم يصبح "زجاجياً":
```css
.glass {
    background: var(--glass-fill);
    border: 1px solid var(--glass-border);
    backdrop-filter: blur(12px);
    border-radius: 16px;
}
```

### 4.3 Staggered Entrance Animation
عند تحميل الصفحة، تظهر العناصر بتتابع:

| العنصر | التأخير | الحركة |
|--------|---------|--------|
| Header | 150ms | `translateY(-12px) → 0` |
| Badge | 320ms | `translateY(20px) → 0` |
| Scene Cards | 480ms + (i × 100ms) | `translateY(20px) → 0` |
| Controls | 800ms | `translateY(20px) → 0` |
| Generate Button | 950ms | `translateY(20px) → 0` |
| Footer | 1100ms | `translateY(20px) → 0` |

```css
.reveal {
    opacity: 0;
    transform: translateY(1.25rem);
    transition: opacity 700ms var(--ease-entrance),
                transform 700ms var(--ease-entrance);
}
.reveal.visible {
    opacity: 1;
    transform: translateY(0);
}
```

---

## 5. تفاصيل التنفيذ

### الملفات المعدّلة

#### [MODIFY] [style.css](file:///e:/tks/backend/static/style.css)
- استبدال كامل النظام اللوني بـ CSS Custom Properties الجديدة
- إضافة `.glass` class لكل العناصر التفاعلية
- إضافة `reveal` animation classes
- إضافة Scrim overlay styling
- تحسين الأزرار لأسلوب pill مع `border-radius: 9999px`
- تحسين Progress Bar بأسلوب زجاجي

#### [MODIFY] [index.html](file:///e:/tks/backend/static/index.html)
- إضافة `<canvas>` للخلفية (أو div بتدرج CSS)
- إضافة Scrim div
- إعادة هيكلة الـ layout بـ `<header>`, `<section>`, `<footer>`
- إضافة classes `.glass` و `.reveal` لكل عنصر

#### [MODIFY] [app.js](file:///e:/tks/backend/static/app.js)
- إضافة staggered reveal logic عند `DOMContentLoaded`
- (اختياري) إضافة WebGL fluid simulation function

---

## 6. ما لن يتم تغييره

> [!IMPORTANT]
> - **لا تغيير في الوظائف أو الـ Backend**
> - **لا تغيير في منطق الـ API أو الـ JS logic**
> - **لا إضافة مكتبات خارجية** (ما عدا Google Font إذا قررنا تغيير الخط)
> - **لا تغيير في هيكل الملفات** — نفس الملفات الثلاثة: `index.html`, `style.css`, `app.js`

---

## 7. الأولوية والترتيب

1. **أولاً**: نظام الألوان الجديد + Glass styling (أسرع تأثير بصري)
2. **ثانياً**: Staggered reveal animations
3. **ثالثاً**: تحسين الـ Layout والـ spacing
4. **رابعاً** (stretch): خلفية WebGL fluid

---

## سؤال مفتوح

> [!WARNING]
> هل تريد تنفيذ خلفية **WebGL Fluid** الكاملة (كود ~400 سطر إضافي في app.js)، أم نكتفي بـ **تدرج CSS متحرك** كبديل سريع وخفيف؟
