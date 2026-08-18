package com.example.stratlearnmobile

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.genai.Client
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * ViewModel managing the business logic and state for the GenAI chat interface.
 */
class AppViewModel : ViewModel() {

    // Internal mutable state
    private val _uiState = MutableStateFlow<UiState>(UiState.Idle)
    
    // Public immutable state exposed to the UI
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()

    // Track the active generation job to allow cancellation
    private var generationJob: Job? = null

    // Initialize the official Google GenAI Client
    // Assumes BuildConfig.GEMINI_API_KEY is properly injected via Gradle
    private val client = Client(BuildConfig.GEMINI_API_KEY)
    
    // The model to use for generation
    private val modelId = "gemini-2.5-flash"

    /**
     * Submits a new prompt to the Gemini model.
     * Cancels any ongoing generation before starting a new one.
     */
    fun submitPrompt(prompt: String) {
        if (prompt.isBlank()) return

        // Cancel previous request if still running
        generationJob?.cancel()

        generationJob = viewModelScope.launch {
            _uiState.value = UiState.Streaming("")

            var accumulatedText = ""
            try {
                // Execute token-by-token streaming
                val responseStream = client.models.generateContentStream(
                    model = modelId,
                    contents = prompt
                )

                // Collect tokens as they arrive
                responseStream.collect { chunk ->
                    chunk.text?.let { newText ->
                        accumulatedText += newText
                        _uiState.update { UiState.Streaming(accumulatedText) }
                    }
                }

                // Streaming finished successfully
                _uiState.value = UiState.Success(accumulatedText)

            } catch (e: Exception) {
                // Handle cancellation or API errors
                if (e is kotlinx.coroutines.CancellationException) {
                    throw e // Re-throw cancellation to let coroutines handle it
                } else {
                    _uiState.value = UiState.Error(e.localizedMessage ?: "An unknown error occurred")
                }
            }
        }
    }

    /**
     * Cancels the current generation job and resets the state to Idle or Success.
     */
    fun cancelGeneration() {
        generationJob?.cancel()
        
        // If we were streaming, just freeze the current state as Success. 
        // Otherwise, return to Idle.
        val currentState = _uiState.value
        if (currentState is UiState.Streaming) {
            _uiState.value = UiState.Success(currentState.partialText)
        } else {
            _uiState.value = UiState.Idle
        }
    }

    /**
     * Resets the UI back to the initial Idle state.
     */
    fun reset() {
        generationJob?.cancel()
        _uiState.value = UiState.Idle
    }
}
