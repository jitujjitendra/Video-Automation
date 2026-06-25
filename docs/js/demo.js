/**
 * Demo Mode Module
 * Provides simulated pipeline output when backend is not available.
 * Used on GitHub Pages to showcase the UI functionality.
 */

const DemoMode = {
    // Whether demo mode is currently active
    isActive: false,

    // Sample output data - a complete Hindi love song example
    sampleOutput: {
        task_id: 'demo-001',
        status: 'completed',
        idea: 'A romantic Hindi love song about monsoon rain in Mumbai',
        language: 'Hindi',
        music_type: 'song',
        steps: {
            script_generation: {
                step: 'script_generation',
                status: 'completed',
                progress_percent: 100,
                message: 'Screenplay generated successfully',
                screenplay: {
                    title: 'Baarish Mein Tum - बारिश में तुम',
                    synopsis: 'A romantic monsoon love story set in Mumbai, where two strangers meet at Marine Drive during a sudden downpour and find an unexpected connection.',
                    mood: 'Romantic, Nostalgic, Dreamy',
                    color_palette: ['Deep Blue', 'Warm Gold', 'Monsoon Grey', 'Rose Pink'],
                    scenes: [
                        {
                            scene_number: 1,
                            scene_type: 'intro',
                            description: 'Aerial shot of Mumbai skyline with dark monsoon clouds gathering. Rain begins to fall over Marine Drive.',
                            visual_prompt: 'Cinematic aerial view of Mumbai Marine Drive during monsoon, dark dramatic clouds, first raindrops hitting the sea, golden hour lighting breaking through clouds, 4K ultra realistic',
                            dialogue: 'बादल आए, घिर के आए, लेके तेरी याद...',
                            duration_seconds: 20,
                            camera_movement: 'slow aerial pan',
                            mood: 'Anticipation'
                        },
                        {
                            scene_number: 2,
                            scene_type: 'verse',
                            description: 'A young woman walks along Marine Drive with an umbrella. She pauses to watch the rain hitting the ocean.',
                            visual_prompt: 'Beautiful Indian woman in turquoise kurti holding transparent umbrella, walking on Marine Drive promenade, monsoon rain, wet road reflections, cinematic depth of field',
                            dialogue: 'भीगी सड़कों पे चलते-चलते, ख्यालों में खो गई...',
                            duration_seconds: 25,
                            camera_movement: 'tracking shot',
                            mood: 'Longing'
                        },
                        {
                            scene_number: 3,
                            scene_type: 'verse',
                            description: 'A young man runs through the rain without an umbrella, laughing. He takes shelter at a bus stop.',
                            visual_prompt: 'Handsome Indian man in white shirt running through heavy monsoon rain on Mumbai street, laughing joyfully, rain droplets in slow motion, warm street lights',
                            dialogue: 'बिन छतरी भीगता कोई, मुस्कुराता जा रहा...',
                            duration_seconds: 20,
                            camera_movement: 'slow motion tracking',
                            mood: 'Joyful'
                        },
                        {
                            scene_number: 4,
                            scene_type: 'chorus',
                            description: 'They both reach the same chai stall. Their eyes meet for the first time over steaming cups of tea.',
                            visual_prompt: 'Two people meeting at a small chai stall in Mumbai rain, warm golden light from stall, steam rising from tea cups, romantic eye contact, bokeh rain in background, cinematic',
                            dialogue: 'बारिश में तुम मिले, जैसे कोई ख्वाब मिले\nदिल ने कहा रुक जा, अभी और नहीं चलना...',
                            duration_seconds: 30,
                            camera_movement: 'slow zoom in',
                            mood: 'Romantic spark'
                        },
                        {
                            scene_number: 5,
                            scene_type: 'verse',
                            description: 'They share the umbrella and walk together along the wet street, talking and laughing.',
                            visual_prompt: 'Couple sharing umbrella walking on wet Mumbai street at night, neon signs reflecting in puddles, romantic atmosphere, rain creating halos around street lights',
                            dialogue: 'एक छतरी में दो राहें, अब तो मिल गईं कहानी...',
                            duration_seconds: 25,
                            camera_movement: 'walking alongside',
                            mood: 'Growing connection'
                        },
                        {
                            scene_number: 6,
                            scene_type: 'chorus',
                            description: 'Back at Marine Drive, they sit on the sea wall watching the rain over the ocean. City lights twinkle behind them.',
                            visual_prompt: 'Romantic couple sitting on Marine Drive sea wall, heavy monsoon rain over Arabian Sea, Mumbai city lights bokeh in background, emotional cinematic composition, golden warm tones',
                            dialogue: 'बारिश में तुम मिले, जैसे कोई ख्वाब मिले\nइस शहर ने दिया तोहफ़ा, बारिश और तुम...',
                            duration_seconds: 30,
                            camera_movement: 'slow crane up',
                            mood: 'Deep romance'
                        },
                        {
                            scene_number: 7,
                            scene_type: 'bridge',
                            description: 'Montage: their hands almost touching, rain drops on a shared phone screen, laughing together at the chai stall.',
                            visual_prompt: 'Close-up romantic montage shots: hands almost touching with rain between them, shared phone screen with rain drops, couple laughing at chai stall, macro rain drops, artistic cinematography',
                            dialogue: 'कितनी बारिशें आईं और गईं\nपर ये वाली दिल में बस गई...',
                            duration_seconds: 20,
                            camera_movement: 'quick cuts with slow motion',
                            mood: 'Emotional peak'
                        },
                        {
                            scene_number: 8,
                            scene_type: 'outro',
                            description: 'The rain stops. A rainbow appears over Marine Drive. They exchange numbers and part ways with a promise to meet again.',
                            visual_prompt: 'Rainbow over Marine Drive Mumbai after monsoon rain, golden sunset breaking through clouds, couple silhouette saying goodbye, cinematic wide shot, hopeful atmosphere',
                            dialogue: 'बारिश रुकी, मगर दिल में बरसात रहे\nफिर मिलेंगे, इसी मोड़ पे, अगली बारिश में...',
                            duration_seconds: 25,
                            camera_movement: 'wide pullback to aerial',
                            mood: 'Hopeful, Bittersweet'
                        }
                    ]
                }
            },
            visual_generation: {
                step: 'visual_generation',
                status: 'completed',
                progress_percent: 100,
                message: 'Visual prompts generated for all scenes',
                data: {
                    visual_prompts: [
                        {
                            scene_number: 1,
                            image_prompt: 'Cinematic aerial photograph of Mumbai Marine Drive during monsoon season, dramatic cumulonimbus clouds, first rain drops creating ripples in Arabian Sea, golden hour sunlight breaking through storm clouds, photorealistic, 8K resolution, dramatic lighting',
                            video_prompt: 'Slow aerial drone shot descending through monsoon clouds revealing Mumbai Marine Drive below, rain beginning to fall, camera slowly panning across the queen necklace of lights, dramatic orchestral mood',
                            negative_prompt: 'cartoon, anime, low quality, blurry, text, watermark',
                            camera_direction: 'Aerial descending pan from clouds to coastline',
                            duration_seconds: 20,
                            aspect_ratio: '16:9'
                        },
                        {
                            scene_number: 2,
                            image_prompt: 'Beautiful young Indian woman wearing turquoise traditional kurti, holding clear transparent umbrella, walking on Marine Drive promenade in monsoon rain, wet concrete reflecting city lights, cinematic bokeh, photorealistic portrait',
                            video_prompt: 'Tracking shot following woman walking with umbrella on rain-soaked Marine Drive, camera at her side, rain in foreground creating depth, slow graceful movement',
                            negative_prompt: 'ugly, distorted face, extra limbs, text, watermark',
                            camera_direction: 'Side tracking shot at walking pace',
                            duration_seconds: 25,
                            aspect_ratio: '16:9'
                        },
                        {
                            scene_number: 4,
                            image_prompt: 'Cozy Mumbai street chai stall with warm golden tungsten lighting, two people meeting over steaming chai cups, monsoon rain pouring in background, steam and warm atmosphere, intimate composition, cinematic color grading',
                            video_prompt: 'Slow push-in shot through rain towards warmly-lit chai stall, revealing two people making eye contact over tea, steam rising between them, romantic cinematic moment',
                            negative_prompt: 'cold colors, ugly, distorted, low quality',
                            camera_direction: 'Slow dolly push towards subjects',
                            duration_seconds: 30,
                            aspect_ratio: '16:9'
                        }
                    ]
                }
            },
            audio_generation: {
                step: 'audio_generation',
                status: 'completed',
                progress_percent: 100,
                message: 'Audio generated for 8 scenes',
                data: {
                    voiceover: {
                        voice_used: 'hi-IN-SwaraNeural',
                        audio_files: [
                            { scene_number: 1, status: 'completed', duration_seconds: 8.2, audio_path: 'outputs/demo/audio/scene_01.mp3' },
                            { scene_number: 2, status: 'completed', duration_seconds: 10.5, audio_path: 'outputs/demo/audio/scene_02.mp3' },
                            { scene_number: 3, status: 'completed', duration_seconds: 8.8, audio_path: 'outputs/demo/audio/scene_03.mp3' },
                            { scene_number: 4, status: 'completed', duration_seconds: 14.2, audio_path: 'outputs/demo/audio/scene_04.mp3' },
                            { scene_number: 5, status: 'completed', duration_seconds: 10.1, audio_path: 'outputs/demo/audio/scene_05.mp3' },
                            { scene_number: 6, status: 'completed', duration_seconds: 13.8, audio_path: 'outputs/demo/audio/scene_06.mp3' },
                            { scene_number: 7, status: 'completed', duration_seconds: 9.4, audio_path: 'outputs/demo/audio/scene_07.mp3' },
                            { scene_number: 8, status: 'completed', duration_seconds: 11.6, audio_path: 'outputs/demo/audio/scene_08.mp3' }
                        ]
                    },
                    suno_guide: {
                        style_tags: 'Bollywood romantic, monsoon vibes, soft acoustic guitar, tabla, flute, emotional vocals',
                        estimated_bpm: 92,
                        lyrics: 'बादल आए, घिर के आए, लेके तेरी याद...\nभीगी सड़कों पे चलते-चलते, ख्यालों में खो गई...\n\n[Chorus]\nबारिश में तुम मिले, जैसे कोई ख्वाब मिले\nदिल ने कहा रुक जा, अभी और नहीं चलना...\n\nएक छतरी में दो राहें, अब तो मिल गईं कहानी...\n\n[Chorus]\nबारिश में तुम मिले, जैसे कोई ख्वाब मिले\nइस शहर ने दिया तोहफ़ा, बारिश और तुम...\n\n[Bridge]\nकितनी बारिशें आईं और गईं\nपर ये वाली दिल में बस गई...\n\n[Outro]\nबारिश रुकी, मगर दिल में बरसात रहे\nफिर मिलेंगे, इसी मोड़ पे, अगली बारिश में...'
                    }
                }
            },
            lipsync: {
                step: 'lipsync',
                status: 'skipped',
                progress_percent: 100,
                message: 'Lip sync available via Colab notebook',
                data: {
                    notebook: {
                        notebook_path: 'colab_notebooks/lipsync_processing.ipynb',
                        instructions: [
                            'Open the notebook in Google Colab',
                            'Switch to T4 GPU runtime',
                            'Upload your video and audio files',
                            'Run all cells to process lip sync'
                        ]
                    }
                }
            },
            editing: {
                step: 'editing',
                status: 'completed',
                progress_percent: 100,
                message: 'Pipeline complete - assets ready',
                data: {
                    assets_available: true,
                    message: 'Demo mode - all assets generated. Install locally and run with your API key for full video assembly.',
                    steps_completed: ['script_generation', 'visual_prompts', 'audio_generation', 'suno_guide']
                }
            }
        }
    },

    /**
     * Run demo mode - simulates the full pipeline with realistic delays.
     * @param {object} settings - User's generation settings.
     * @param {function} onProgress - Callback for progress updates.
     * @param {function} onComplete - Callback when demo completes.
     */
    async runDemoMode(settings, onProgress, onComplete) {
        this.isActive = true;
        this.showDemoBadge();

        const steps = [
            {
                step: 'script_generation',
                messages: [
                    { msg: 'Analyzing your idea...', pct: 10 },
                    { msg: 'Generating lyrics and storyline...', pct: 40 },
                    { msg: 'Creating scene-by-scene screenplay...', pct: 70 },
                    { msg: 'Screenplay generated successfully', pct: 100 }
                ],
                delay: 800
            },
            {
                step: 'visual_generation',
                messages: [
                    { msg: 'Analyzing scenes for visual composition...', pct: 15 },
                    { msg: 'Generating image prompts for AI art...', pct: 45 },
                    { msg: 'Creating video motion descriptions...', pct: 75 },
                    { msg: 'Visual prompts generated for all scenes', pct: 100 }
                ],
                delay: 600
            },
            {
                step: 'audio_generation',
                messages: [
                    { msg: 'Selecting voice for language...', pct: 10 },
                    { msg: 'Generating voiceover for Scene 1-3...', pct: 35 },
                    { msg: 'Generating voiceover for Scene 4-6...', pct: 65 },
                    { msg: 'Generating voiceover for Scene 7-8...', pct: 85 },
                    { msg: 'Audio generated for 8 scenes', pct: 100 }
                ],
                delay: 700
            },
            {
                step: 'lipsync',
                messages: [
                    { msg: 'Lip sync available via Colab notebook', pct: 100 }
                ],
                delay: 300,
                skipStatus: true
            },
            {
                step: 'editing',
                messages: [
                    { msg: 'Assembling project assets...', pct: 30 },
                    { msg: 'Creating download package...', pct: 70 },
                    { msg: 'Pipeline complete - assets ready', pct: 100 }
                ],
                delay: 500
            }
        ];

        for (const stepInfo of steps) {
            for (const update of stepInfo.messages) {
                await this._delay(stepInfo.delay);

                const progressData = {
                    step: stepInfo.step,
                    status: update.pct === 100 ? 'completed' : 'in_progress',
                    progress_percent: update.pct,
                    message: update.msg
                };

                if (stepInfo.skipStatus && update.pct === 100) {
                    progressData.status = 'skipped';
                }

                if (onProgress) {
                    onProgress(progressData);
                }
            }
        }

        // Complete with demo data
        await this._delay(500);
        if (onComplete) {
            onComplete(this.sampleOutput);
        }

        this.isActive = false;
    },

    /**
     * Show the demo mode badge in the UI.
     */
    showDemoBadge() {
        // Remove existing badge if any
        const existing = document.getElementById('demo-badge');
        if (existing) existing.remove();

        const badge = document.createElement('div');
        badge.id = 'demo-badge';
        badge.innerHTML = 'DEMO';
        badge.style.cssText = `
            position: fixed;
            top: 12px;
            right: 12px;
            background: linear-gradient(135deg, #ff6b6b, #ff8e53);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
            letter-spacing: 1px;
            z-index: 10000;
            box-shadow: 0 2px 8px rgba(255, 107, 107, 0.4);
            animation: demoPulse 2s infinite;
        `;

        // Add animation
        if (!document.getElementById('demo-badge-style')) {
            const style = document.createElement('style');
            style.id = 'demo-badge-style';
            style.textContent = `
                @keyframes demoPulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.7; }
                }
            `;
            document.head.appendChild(style);
        }

        document.body.appendChild(badge);
    },

    /**
     * Hide the demo mode badge.
     */
    hideDemoBadge() {
        const badge = document.getElementById('demo-badge');
        if (badge) badge.remove();
    },

    /**
     * Utility: async delay.
     * @param {number} ms - Milliseconds to wait.
     */
    _delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};
