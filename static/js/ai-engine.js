// Onion Lens - Real AI Inspection & Computer Vision Engine
// Connects directly to the FastAPI backend running OpenCV watershed segmentation & defect analysis
// NO Math.random() - All results are calculated from real image pixel measurements!

const AIEngine = {
    analyzeImage: async function(imageSource, lotDetails = {}, onProgress = null) {
        if (onProgress) onProgress(20, 'proc_step1');

        let dataUrl = '';
        if (typeof imageSource === 'string') {
            dataUrl = imageSource;
        } else if (imageSource instanceof HTMLImageElement || imageSource instanceof HTMLCanvasElement) {
            const canvas = document.createElement('canvas');
            canvas.width = imageSource.naturalWidth || imageSource.width || 640;
            canvas.height = imageSource.naturalHeight || imageSource.height || 640;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(imageSource, 0, 0, canvas.width, canvas.height);
            dataUrl = canvas.toDataURL('image/jpeg', 0.90);
        }

        if (onProgress) onProgress(50, 'proc_step2');

        try {
            // Call real FastAPI CV endpoint
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    image: dataUrl,
                    lot_id: lotDetails.lotId || null,
                    variety: lotDetails.variety || 'Nashik Red',
                    quantity_kg: lotDetails.quantityKg || '500 kg',
                    inspector: lotDetails.inspector || 'Inspector (Procurement Centre)'
                })
            });

            if (onProgress) onProgress(80, 'proc_step3');

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || 'Analysis server returned an error (' + response.status + ')');
            }

            const data = await response.json();
            if (onProgress) onProgress(100, 'proc_step5');

            // Map server fields to frontend structure
            return {
                id: data.inspection_id,
                isOnion: data.is_onion,
                errorMessage: data.error_message,
                lotId: data.lot_id,
                timestamp: data.timestamp,
                dateFormatted: new Date(data.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
                quantityKg: lotDetails.quantityKg || '500 kg',
                variety: lotDetails.variety || 'Nashik Red',
                inspector: lotDetails.inspector || 'Inspector (Procurement Centre)',
                grade: data.grade,
                gradeName: data.grade_name,
                gradeBadgeClass: data.grade_badge_class,
                qualityScore: data.quality_score,
                bulbCount: data.total_onions,
                totalOnions: data.total_onions,
                healthyOnions: data.healthy_onions,
                defectiveOnions: data.defective_onions,
                gradeCounts: (() => {
                    const bulbs = data.individual_bulbs || [];
                    const countA = bulbs.filter(b => b.grade === 'GRADE_A').length;
                    const countU = bulbs.filter(b => b.grade === 'URS').length;
                    const countNE = bulbs.filter(b => b.grade === 'NOT_ELIGIBLE').length;
                    return {
                        gradeA: countA,
                        urs: countU,
                        notEligible: countNE,
                        total: bulbs.length || data.total_onions || 1
                    };
                })(),
                individualBulbs: (data.individual_bulbs || []).map(b => ({
                    id: b.onion_id,
                    grade: b.grade,
                    gradeName: b.grade_name,
                    gradeBadgeClass: b.grade_badge_class,
                    diameter: b.diameter_mm,
                    issues: b.issues,
                    x: b.center_x_pct,
                    y: b.center_y_pct,
                    isHealthy: b.is_healthy,
                    defects: b.defects || []
                })),
                avgDiameter: data.avg_diameter,
                colorUniformity: data.color_uniformity,
                defects: data.defect_percentages || {
                    sprouting: '0%',
                    blackMold: '0%',
                    rotDecay: '0%',
                    cutsBruises: '0%',
                    skinPeeling: '0%'
                },
                defectCounts: data.defect_counts || {
                    sprouting: 0,
                    mold: 0,
                    mechanical_damage: 0,
                    skin_peeling: 0,
                    undersized: 0
                },
                defectSummaries: data.defects || [],
                hotspots: data.hotspots || [],
                recommendations: data.recommendations || [],
                aiModelStatus: data.ai_model_status,
                aiModelBackend: data.ai_model_backend
            };

        } catch (err) {
            console.error('[AI ENGINE ERROR]', err);
            // Return clear error without faking results
            return {
                id: 'ERR-' + Date.now(),
                isOnion: false,
                lotId: lotDetails.lotId || 'LOT-ERR',
                timestamp: new Date().toISOString(),
                dateFormatted: new Date().toLocaleDateString('en-US'),
                errorMessage: 'Computer Vision analysis could not connect to server. Check server status: ' + err.message,
                totalOnions: 0,
                healthyOnions: 0,
                defectiveOnions: 0,
                grade: 'NOT_ELIGIBLE',
                gradeName: 'Error',
                gradeBadgeClass: 'badge-not-eligible',
                qualityScore: 0,
                bulbCount: 0,
                individualBulbs: [],
                hotspots: [],
                recommendations: ['Ensure local FastAPI server is running on port 8000.']
            };
        }
    }
};
