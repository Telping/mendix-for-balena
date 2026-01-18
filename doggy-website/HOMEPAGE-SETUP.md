# Homepage Setup with Boxty's Photo

## What I Added

The homepage now features a beautiful hero section with Boxty's photo!

### Hero Section Layout

```
┌─────────────────────────────────────────────────────┐
│  ┌─────────┐  ┌────────────────────────────────┐   │
│  │         │  │  🐾 Boxty's Adventures         │   │
│  │ Boxty's │  │                                 │   │
│  │  Photo  │  │  Welcome to Boxty's digital    │   │
│  │         │  │  diary! Follow along...        │   │
│  │         │  │                                 │   │
│  └─────────┘  │  [Add New Memory]  [View Map]  │   │
│               └────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

The hero section appears at the top of every homepage visit and includes:
- Boxty's adorable photo on the left
- Welcome message and description
- Quick action buttons to add memories or view the map

## Adding Boxty's Photo

### Option 1: Use the Helper Script (Easiest)

```bash
./add-boxty-photo.sh
```

Then follow the prompts to select one of Boxty's photos!

### Option 2: Manual Copy

```bash
# Save one of Boxty's photos as:
cp /path/to/boxty-photo.jpg app/static/images/boxty-hero.jpg
```

### Option 3: Download from Your Images

If you have the images saved from our conversation:
1. Locate the Boxty photos on your computer
2. Choose your favorite one (I love the one being held in the hand!)
3. Save it as `boxty-hero.jpg` in `app/static/images/`

## What Happens if No Photo?

Don't worry! If the photo isn't there yet, the homepage shows a nice placeholder with a dog emoji (🐕) on a chocolate brown background - still looks great!

## Customizing the Hero Section

Want to change the text? Edit [app/templates/index.html](app/templates/index.html):

```html
<h1 class="card-title display-4 paw-icon">Boxty's Adventures</h1>
<p class="card-text lead">
    Welcome to Boxty's digital diary! Follow along as we document the amazing
    journey of the most adorable pup. Every photo, every place, every precious moment.
</p>
```

Change it to whatever you like!

## Styling

The hero section includes:
- Gradient background (white to cream)
- Chocolate brown border (matching Boxty's color!)
- Responsive design (looks great on mobile too)
- Automatic image sizing and cropping

### Want different colors?

Edit [app/templates/base.html](app/templates/base.html):

```css
.hero-card {
    background: linear-gradient(135deg, #fff 0%, #FFF8DC 100%);
    border: 2px solid var(--boxty-light);
}
```

## See It in Action

1. Add Boxty's photo (using one of the methods above)
2. Start the app:
   ```bash
   ./start-local.sh
   ```
3. Open http://localhost:5000
4. Enjoy seeing Boxty's cute face welcoming you!

## Tips

- **Best Photo Size**: 800x600 pixels or larger
- **Format**: JPG works best (smaller file size)
- **Aspect Ratio**: Any ratio works - the CSS will crop nicely
- **File Size**: Keep under 2MB for fast loading

## What's Next?

After adding the hero photo, you might want to:
1. Create your first diary entry with more Boxty photos
2. Customize the welcome message
3. Add tags for different types of adventures
4. Start building that adorable timeline!

---

Can't wait to see Boxty's face on the homepage! 🐾
