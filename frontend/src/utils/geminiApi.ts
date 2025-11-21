/**
 * Gemini API Helper for Analysis Recommendation
 */

interface GeminiAnalysisResponse {
    response_type: 'analysis_recommendation';
    data: {
        recommendations: Array<{
            analysis_type: 'structural' | 'thermal' | 'magnetostatic' | 'modal';
            confidence: number;
            reasoning: string;
        }>;
        parameters_suggestion?: {
            [key: string]: string | number;
        };
    };
}

const ANALYSIS_INSTRUCTION = `You are an expert CAE (Computer-Aided Engineering) analyst. Your task is to recommend the TOP 3 most suitable finite element analysis types based on the user's description and/or uploaded file.

Available Analysis Types:
1. **Static Structural Analysis** - For analyzing stress, displacement, and deformation under static loads. Use when:
   - User mentions: stress, strength, force, load, deformation, displacement, von Mises, static loading
   - Component experiences constant/static forces
   - Need to evaluate structural integrity

2. **Thermal Analysis** - For heat transfer and temperature distribution. Use when:
   - User mentions: temperature, heat, thermal, cooling, heating, conduction, convection
   - Need to analyze temperature distribution
   - Heat dissipation or thermal management problems

3. **Magnetostatic Analysis** - For electromagnetic field analysis. Use when:
   - User mentions: magnetic, electromagnetic, flux, coil, magnet, inductor, motor, solenoid
   - Analyzing magnetic fields, forces, or torques
   - Electromagnetic components or devices

4. **Modal Analysis** - For vibration and frequency response. Use when:
   - User mentions: vibration, resonance, frequency, mode shapes, natural frequency, dynamic
   - Need to find natural frequencies
   - Avoiding resonance issues

CRITICAL: You MUST respond with ONLY a valid JSON object. Do NOT include any markdown formatting, code blocks, or explanatory text.
Do NOT wrap your response in backticks or any other formatting.
Your ENTIRE response must be ONLY this JSON structure - nothing before it, nothing after it:

{
  "response_type": "analysis_recommendation",
  "data": {
    "recommendations": [
      {
        "analysis_type": "structural",
        "confidence": 0.85,
        "reasoning": "Primary recommendation - component under mechanical load requires stress analysis"
      },
      {
        "analysis_type": "modal",
        "confidence": 0.65,
        "reasoning": "Secondary recommendation - may need vibration analysis if dynamic loads present"
      },
      {
        "analysis_type": "thermal",
        "confidence": 0.45,
        "reasoning": "Tertiary recommendation - consider if heat generation is a concern"
      }
    ],
    "parameters_suggestion": {
      "mesh_size": "5",
      "force_magnitude": "1000",
      "material": "Steel"
    }
  }
}

RULES:
- MUST provide exactly 3 recommendations in order of confidence (highest to lowest)
- Each analysis_type must be one of: "structural", "thermal", "magnetostatic", "modal"
- Each confidence must be a number between 0.0 and 1.0
- First recommendation should have highest confidence, third should have lowest
- Provide specific reasoning for each recommendation
- parameters_suggestion should apply to the top recommendation
- Do NOT use markdown formatting
- Do NOT include code blocks with backticks
- Return ONLY the JSON object`;

export async function getAnalysisRecommendation(
    userDescription: string,
    fileName?: string
): Promise<GeminiAnalysisResponse> {
    const apiKey = import.meta.env.VITE_GOOGLE_GEMINI_API_KEY;

    if (!apiKey) {
        throw new Error('Gemini API key not configured. Please add VITE_GOOGLE_GEMINI_API_KEY to your .env file');
    }

    const fullPrompt = `${ANALYSIS_INSTRUCTION}

${fileName ? `Uploaded file: ${fileName}` : ''}

User description: "${userDescription}"

Respond with ONLY the JSON object, no other text.`;

    try {
        const response = await fetch(
            `https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: [{ parts: [{ text: fullPrompt }] }],
                    generationConfig: {
                        temperature: 0.2,
                        topK: 20,
                        topP: 0.8,
                        maxOutputTokens: 2048,
                    },
                }),
                signal: AbortSignal.timeout(30000), // 30 seconds timeout
            }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: 'No body from Gemini API' }));
            console.error('Gemini API error:', response.status, errorData);
            throw new Error(`Gemini API call failed: ${response.status} - ${JSON.stringify(errorData)}`);
        }

        const data = await response.json();

        // Log the full response for debugging
        console.log('Full Gemini API response (text):', data);

        // Validate response structure
        if (!data.candidates || data.candidates.length === 0) {
            console.error('Gemini API response has no candidates:', data);
            throw new Error('Gemini API response is malformed or empty');
        }

        const candidate = data.candidates[0];

        // Check if response was truncated
        if (candidate.finishReason === 'MAX_TOKENS') {
            console.error('Gemini response hit token limit:', candidate);
            throw new Error('AI response was too long and got cut off. Please try with a shorter description.');
        }

        if (!candidate.content) {
            console.error('Gemini API candidate has no content:', candidate);
            throw new Error('Gemini API response is malformed or empty');
        }

        if (!candidate.content.parts || candidate.content.parts.length === 0) {
            console.error('Gemini API candidate has no content parts:', candidate);
            console.error('Finish reason:', candidate.finishReason);
            throw new Error('Gemini API response is malformed or empty. Finish reason: ' + candidate.finishReason);
        }

        // Get the text from the first part
        const geminiResponse = candidate.content.parts[0].text;

        if (!geminiResponse) {
            console.error('Gemini API response has no text in parts[0]:', candidate.content.parts[0]);
            console.error('Full parts:', candidate.content.parts);
            throw new Error('Gemini API response text is empty or missing');
        }

        // Parse JSON response - with responseMimeType set to application/json, it should be direct JSON
        try {
            // Clean the response string
            let jsonString = geminiResponse.trim();

            // Remove markdown code blocks if present (fallback for older API versions)
            const codeBlockMatch = jsonString.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
            if (codeBlockMatch) {
                jsonString = codeBlockMatch[1].trim();
            }

            // Remove any leading/trailing non-JSON characters
            const jsonMatch = jsonString.match(/(\{[\s\S]*\})/);
            if (jsonMatch) {
                jsonString = jsonMatch[1];
            }

            const parsedResponse: GeminiAnalysisResponse = JSON.parse(jsonString);

            // Validate response structure
            if (!parsedResponse.response_type || parsedResponse.response_type !== 'analysis_recommendation') {
                console.error('Invalid response_type:', parsedResponse);
                throw new Error('Response missing required response_type field');
            }

            if (!parsedResponse.data || !parsedResponse.data.recommendations || !Array.isArray(parsedResponse.data.recommendations)) {
                console.error('Invalid data structure:', parsedResponse);
                throw new Error('Response missing required recommendations array');
            }

            // Validate we have exactly 3 recommendations
            if (parsedResponse.data.recommendations.length !== 3) {
                console.error('Invalid number of recommendations:', parsedResponse.data.recommendations.length);
                throw new Error('Response must contain exactly 3 recommendations');
            }

            // Validate each recommendation
            const validAnalyses = ['structural', 'thermal', 'magnetostatic', 'modal'];
            parsedResponse.data.recommendations.forEach((rec, index) => {
                if (!rec.analysis_type || !validAnalyses.includes(rec.analysis_type)) {
                    throw new Error(`Invalid analysis_type at index ${index}: ${rec.analysis_type}`);
                }
                if (typeof rec.confidence !== 'number' || rec.confidence < 0 || rec.confidence > 1) {
                    throw new Error(`Invalid confidence at index ${index}: ${rec.confidence}`);
                }
                if (!rec.reasoning) {
                    throw new Error(`Missing reasoning at index ${index}`);
                }
            });

            return parsedResponse;
        } catch (parseError) {
            console.error('Error parsing Gemini JSON:', parseError);
            console.error('Raw Gemini response:', geminiResponse);
            throw new Error(`Failed to parse Gemini response as valid JSON: ${parseError instanceof Error ? parseError.message : 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Gemini API error:', error);
        throw error;
    }
}

export async function getAnalysisRecommendationWithImage(
    userDescription: string,
    imageFile: File
): Promise<GeminiAnalysisResponse> {
    const apiKey = import.meta.env.VITE_GOOGLE_GEMINI_API_KEY;

    if (!apiKey) {
        throw new Error('Gemini API key not configured');
    }

    // Convert image to base64
    const base64Image = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            const base64 = reader.result as string;
            // Remove data URL prefix
            const base64Data = base64.split(',')[1];
            resolve(base64Data);
        };
        reader.onerror = reject;
        reader.readAsDataURL(imageFile);
    });

    const fullPrompt = `${ANALYSIS_INSTRUCTION}

Image file: ${imageFile.name}

User description: "${userDescription}"

Respond with ONLY the JSON object, no other text.`;

    try {
        const response = await fetch(
            `https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    contents: [{
                        parts: [
                            { text: fullPrompt },
                            {
                                inline_data: {
                                    mime_type: imageFile.type,
                                    data: base64Image
                                }
                            }
                        ]
                    }],
                    generationConfig: {
                        temperature: 0.2,
                        topK: 20,
                        topP: 0.8,
                        maxOutputTokens: 2048,
                    },
                }),
                signal: AbortSignal.timeout(30000),
            }
        );

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: 'No body from Gemini API' }));
            console.error('Gemini API error:', response.status, errorData);
            throw new Error(`Gemini API call failed: ${response.status}`);
        }

        const data = await response.json();

        // Log the full response for debugging
        console.log('Full Gemini API response (image):', data);

        // Validate response structure
        if (!data.candidates || data.candidates.length === 0) {
            console.error('Gemini API response has no candidates:', data);
            throw new Error('Gemini API response is malformed or empty');
        }

        const candidate = data.candidates[0];

        // Check if response was truncated
        if (candidate.finishReason === 'MAX_TOKENS') {
            console.error('Gemini response hit token limit:', candidate);
            throw new Error('AI response was too long and got cut off. The image analysis is taking too many tokens. Please try with a simpler image or more concise description.');
        }

        if (!candidate.content) {
            console.error('Gemini API candidate has no content:', candidate);
            throw new Error('Gemini API response is malformed or empty');
        }

        if (!candidate.content.parts || candidate.content.parts.length === 0) {
            console.error('Gemini API candidate has no content parts:', candidate);
            console.error('Finish reason:', candidate.finishReason);
            throw new Error('Gemini API response is malformed or empty. Finish reason: ' + candidate.finishReason);
        }

        // Get the text from the first part
        const geminiResponse = candidate.content.parts[0].text;

        if (!geminiResponse) {
            console.error('Gemini API response has no text in parts[0]:', candidate.content.parts[0]);
            console.error('Full parts:', candidate.content.parts);
            throw new Error('Gemini API response text is empty or missing');
        }

        // Parse JSON response with same robust parsing as text-only function
        try {
            let jsonString = geminiResponse.trim();

            // Remove markdown code blocks if present
            const codeBlockMatch = jsonString.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
            if (codeBlockMatch) {
                jsonString = codeBlockMatch[1].trim();
            }

            // Remove any leading/trailing non-JSON characters
            const jsonMatch = jsonString.match(/(\{[\s\S]*\})/);
            if (jsonMatch) {
                jsonString = jsonMatch[1];
            }

            const parsedResponse: GeminiAnalysisResponse = JSON.parse(jsonString);

            // Validate response structure
            if (!parsedResponse.response_type || parsedResponse.response_type !== 'analysis_recommendation') {
                console.error('Invalid response_type:', parsedResponse);
                throw new Error('Response missing required response_type field');
            }

            if (!parsedResponse.data || !parsedResponse.data.recommendations || !Array.isArray(parsedResponse.data.recommendations)) {
                console.error('Invalid data structure:', parsedResponse);
                throw new Error('Response missing required recommendations array');
            }

            // Validate we have exactly 3 recommendations
            if (parsedResponse.data.recommendations.length !== 3) {
                console.error('Invalid number of recommendations:', parsedResponse.data.recommendations.length);
                throw new Error('Response must contain exactly 3 recommendations');
            }

            // Validate each recommendation
            const validAnalyses = ['structural', 'thermal', 'magnetostatic', 'modal'];
            parsedResponse.data.recommendations.forEach((rec, index) => {
                if (!rec.analysis_type || !validAnalyses.includes(rec.analysis_type)) {
                    throw new Error(`Invalid analysis_type at index ${index}: ${rec.analysis_type}`);
                }
                if (typeof rec.confidence !== 'number' || rec.confidence < 0 || rec.confidence > 1) {
                    throw new Error(`Invalid confidence at index ${index}: ${rec.confidence}`);
                }
                if (!rec.reasoning) {
                    throw new Error(`Missing reasoning at index ${index}`);
                }
            });

            return parsedResponse;
        } catch (parseError) {
            console.error('Error parsing Gemini JSON:', parseError);
            console.error('Raw Gemini response:', geminiResponse);
            throw new Error(`Failed to parse Gemini response as valid JSON: ${parseError instanceof Error ? parseError.message : 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Gemini API error with image:', error);
        throw error;
    }
}
