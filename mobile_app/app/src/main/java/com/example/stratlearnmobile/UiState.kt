package com.example.stratlearnmobile

/**
 * Represents the immutable UI state of the GenAI chat interface.
 * Implements a Unidirectional Data Flow (UDF) pattern.
 */
sealed interface UiState {
    /**
     * The initial state, ready for the user to input a prompt.
     */
    data object Idle : UiState

    /**
     * Active token generation state.
     * @param partialText The accumulated text received from the stream so far.
     */
    data class Streaming(val partialText: String) : UiState

    /**
     * Completed output state.
     * @param fullResponse The complete generated text.
     */
    data class Success(val fullResponse: String) : UiState

    /**
     * Error state for API issues, connectivity failures, etc.
     * @param message Human-readable error description.
     */
    data class Error(val message: String) : UiState
}
