package com.example.stratlearnmobile

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle

/**
 * Main adaptive UI screen handling both Compact (Phones) and Expanded (Tablets) layouts.
 */
@Composable
fun MainScreen(viewModel: AppViewModel) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val configuration = LocalConfiguration.current
    
    // Simple breakpoint for Adaptive UI (600dp is typical for Tablets/Foldables)
    val isExpanded = configuration.screenWidthDp > 600

    Scaffold(
        modifier = Modifier
            .fillMaxSize()
            .safeDrawingPadding()
    ) { paddingValues ->
        if (isExpanded) {
            ExpandedLayout(
                uiState = uiState,
                onSubmit = { viewModel.submitPrompt(it) },
                onCancel = { viewModel.cancelGeneration() },
                modifier = Modifier.padding(paddingValues)
            )
        } else {
            CompactLayout(
                uiState = uiState,
                onSubmit = { viewModel.submitPrompt(it) },
                onCancel = { viewModel.cancelGeneration() },
                modifier = Modifier.padding(paddingValues)
            )
        }
    }
}

@Composable
fun CompactLayout(
    uiState: UiState,
    onSubmit: (String) -> Unit,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp)
    ) {
        // Output Area (Scrollable)
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
        ) {
            OutputArea(uiState)
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        // Input Area (Sticky at bottom)
        InputArea(
            isGenerating = uiState is UiState.Streaming,
            onSubmit = onSubmit,
            onCancel = onCancel
        )
    }
}

@Composable
fun ExpandedLayout(
    uiState: UiState,
    onSubmit: (String) -> Unit,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        // Left Pane: Input Area
        Column(
            modifier = Modifier
                .weight(1f)
                .fillMaxHeight(),
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "StratLearn Assistant",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(bottom = 16.dp)
            )
            InputArea(
                isGenerating = uiState is UiState.Streaming,
                onSubmit = onSubmit,
                onCancel = onCancel
            )
        }

        // Right Pane: Output Area
        Card(
            modifier = Modifier
                .weight(2f)
                .fillMaxHeight(),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.surfaceVariant
            )
        ) {
            Box(modifier = Modifier.padding(24.dp)) {
                OutputArea(uiState)
            }
        }
    }
}

@Composable
fun OutputArea(uiState: UiState) {
    val scrollState = rememberScrollState()

    // Auto-scroll to bottom when state changes (new tokens arrive)
    LaunchedEffect(uiState) {
        if (uiState is UiState.Streaming || uiState is UiState.Success) {
            scrollState.animateScrollTo(scrollState.maxValue)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(scrollState)
    ) {
        when (uiState) {
            is UiState.Idle -> {
                Text(
                    text = "Hello! How can I help you today?",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            is UiState.Streaming -> {
                Text(
                    text = uiState.partialText,
                    style = MaterialTheme.typography.bodyLarge
                )
                CircularProgressIndicator(
                    modifier = Modifier
                        .padding(top = 16.dp)
                        .size(24.dp),
                    strokeWidth = 2.dp
                )
            }
            is UiState.Success -> {
                Text(
                    text = uiState.fullResponse,
                    style = MaterialTheme.typography.bodyLarge
                )
            }
            is UiState.Error -> {
                Text(
                    text = "Error: ${uiState.message}",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.error
                )
            }
        }
    }
}

@Composable
fun InputArea(
    isGenerating: Boolean,
    onSubmit: (String) -> Unit,
    onCancel: () -> Unit
) {
    var prompt by remember { mutableStateOf("") }

    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        OutlinedTextField(
            value = prompt,
            onValueChange = { prompt = it },
            placeholder = { Text("Ask anything...") },
            modifier = Modifier.weight(1f),
            maxLines = 4,
            shape = MaterialTheme.shapes.extraLarge
        )
        
        Spacer(modifier = Modifier.width(8.dp))
        
        if (isGenerating) {
            FilledIconButton(
                onClick = { onCancel() },
                modifier = Modifier.size(48.dp),
                colors = IconButtonDefaults.filledIconButtonColors(
                    containerColor = MaterialTheme.colorScheme.errorContainer,
                    contentColor = MaterialTheme.colorScheme.onErrorContainer
                )
            ) {
                Icon(Icons.Default.Stop, contentDescription = "Stop Generation")
            }
        } else {
            FilledIconButton(
                onClick = { 
                    if (prompt.isNotBlank()) {
                        onSubmit(prompt)
                        prompt = ""
                    }
                },
                modifier = Modifier.size(48.dp)
            ) {
                Icon(Icons.AutoMirrored.Filled.Send, contentDescription = "Send Prompt")
            }
        }
    }
}
