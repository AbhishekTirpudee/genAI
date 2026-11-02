export const STYLES = [
  {
    id: "photorealistic",
    name: "Photorealistic",
    category: "Realism",
    emoji: "📸",
    badge: "Popular",
    description: "8k ultra-sharp photography with natural lighting & rich textures",
    example: "A majestic snow leopard resting on Himalayan peaks at sunrise"
  },
  {
    id: "cinematic",
    name: "Cinematic Film",
    category: "Realism",
    emoji: "🎬",
    badge: "Trending",
    description: "Dramatic movie still with anamorphic bokeh & color grade",
    example: "A lone explorer gazing at towering ancient monolithic ruins in mist"
  },
  {
    id: "anime",
    name: "Anime & Manga",
    category: "Illustration",
    emoji: "🌸",
    badge: "Popular",
    description: "Makoto Shinkai & Ghibli aesthetic with expressive colors",
    example: "A magical apothecary shop nestled under a giant blooming cherry tree"
  },
  {
    id: "cyberpunk",
    name: "Cyberpunk",
    category: "Sci-Fi",
    emoji: "🌆",
    badge: "Vibrant",
    description: "Neon drenched cityscape, holographic glare & ray tracing",
    example: "A futuristic night market with hovering neon food stalls in the rain"
  },
  {
    id: "fantasy",
    name: "Epic Fantasy",
    category: "Artistic",
    emoji: "✨",
    badge: "Ethereal",
    description: "Mystical floating islands, ethereal glow & golden hour light",
    example: "An ancient wizard castle perched on a floating crystalline asteroid"
  },
  {
    id: "3d_render",
    name: "3D Pixar Style",
    category: "3D",
    emoji: "🧸",
    badge: "Cute",
    description: "Polished Octane 3D render with soft lighting and subsurface glow",
    example: "A curious baby dragon wearing aviator goggles learning to fly"
  },
  {
    id: "oil_painting",
    name: "Oil Painting",
    category: "Fine Art",
    emoji: "🎨",
    badge: "Classic",
    description: "Heavy palette knife impasto, deep textural chiaroscuro depth",
    example: "A dramatic stormy galleon ship navigating tempestuous ocean waves"
  },
  {
    id: "digital_art",
    name: "Digital Art",
    category: "Artistic",
    emoji: "🖌️",
    badge: "Modern",
    description: "Vibrant ArtStation trending concept art with crisp detail",
    example: "A cyberpunk samurai warrior dueling with an energy katana"
  },
  {
    id: "watercolor",
    name: "Watercolor",
    category: "Fine Art",
    emoji: "🌊",
    badge: "Delicate",
    description: "Wet-on-wet watercolor washes on cold-press cotton paper",
    example: "A quaint Venetian canal at dusk with glowing lantern reflections"
  },
  {
    id: "studio_portrait",
    name: "Studio Portrait",
    category: "Realism",
    emoji: "👤",
    badge: "Editorial",
    description: "Editorial beauty portrait with softbox lighting and 85mm lens",
    example: "A fashion portrait of a model with iridescent crystalline makeup"
  },
  {
    id: "pixel_art",
    name: "16-Bit Pixel Art",
    category: "Retro",
    emoji: "👾",
    badge: "Retro",
    description: "Nostalgic retro video game sprites with clean pixel grids",
    example: "A cozy tavern interior in a fantasy RPG town with a crackling fireplace"
  },
  {
    id: "none",
    name: "Natural / Raw",
    category: "Direct",
    emoji: "🎯",
    badge: "Exact",
    description: "Direct FLUX model interpretation without style modifier words",
    example: "A hyper-detailed mechanical watch movement in macro view"
  }
];

export const ASPECT_RATIOS = [
  { id: "1:1", label: "1:1 Square", width: 1024, height: 1024, icon: "Square", desc: "Best for Avatars & Social" },
  { id: "16:9", label: "16:9 Landscape", width: 1280, height: 720, icon: "Monitor", desc: "Best for Wallpapers & Cinematic" },
  { id: "9:16", label: "9:16 Portrait", width: 720, height: 1280, icon: "Smartphone", desc: "Best for Stories & Mobile" },
  { id: "4:3", label: "4:3 Classic", width: 1024, height: 768, icon: "Tv", desc: "Best for Art & Photography" }
];

export const SAMPLE_PROMPTS = [
  "A majestic snow leopard resting on Himalayan peaks at golden sunrise",
  "A cyberpunk night street food vendor with glowing holographic menus in Tokyo",
  "A mystical tree of life with glowing roots in an enchanted crystalline cavern",
  "Cute baby red panda wearing tiny astronaut suit walking on the Moon, 3d render",
  "Victorian steampunk airship soaring over London through twilight clouds",
  "A cozy cabin surrounded by bioluminescent pine forest under aurora borealis",
  "An ancient library with endless spiraling bookshelves and floating books",
  "Futuristic electric sports car racing on a rainbow neon track in the sky"
];

export const GENERATION_TIPS = [
  "FLUX.1-schnell excels at lighting, complex textures, and typography.",
  "Specifying lighting (e.g. 'volumetric rays', 'dusk lighting') improves realism.",
  "Using 4 inference steps produces optimal speed and quality balance on FLUX.",
  "Pillow converts the raw tensor into an optimized, lossless PNG format.",
  "Each generated PNG contains full RGB color fidelity."
];

