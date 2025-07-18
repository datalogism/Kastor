import torch
import torch.nn as nn
import torch.nn.functional as F


class ManualCE0(nn.CrossEntropyLoss):
    """
    Custom cross-entropy loss implementation that handles padding tokens and optional class weights.
    This class extends PyTorch's CrossEntropyLoss with additional functionality.
    """

    def __init__(self, weights=None, device=None):
        """
        Initialize the ManualCE0 loss function.

        Args:
            weights (torch.Tensor, optional): Class weights for handling class imbalance.
            device (torch.device, optional): Device to perform computations on (e.g., 'cuda' or 'cpu').
        """
        super(ManualCE0, self).__init__()
        self.weights = weights
        self.device = device

    def forward(self, inputs, targets):
        """
        Compute the cross-entropy loss while ignoring padding tokens.

        Args:
            inputs (torch.Tensor): Model predictions with shape [batch_size, seq_len, vocab_size]
            targets (torch.Tensor): Ground truth labels with shape [batch_size, seq_len]

        Returns:
            torch.Tensor: Computed loss value (scalar)
        """
        batch_size, seq_len, vocab_size = inputs.shape

        # Flatten logits and labels for easier processing
        logits_flat = inputs.view(-1, vocab_size)  # shape: [batch_size * seq_len, vocab_size]
        labels_flat = targets.view(-1)  # shape: [batch_size * seq_len]

        # Create mask to identify and ignore padding tokens (marked with -100)
        mask = labels_flat != -100  # shape: [batch_size * seq_len], boolean mask

        # Filter out padding positions from both logits and labels
        logits_filtered = logits_flat[mask]  # shape: [valid_positions, vocab_size]
        labels_filtered = labels_flat[mask]  # shape: [valid_positions]

        # Compute log probabilities using log softmax for numerical stability
        log_probs = F.log_softmax(logits_filtered, dim=-1)  # shape: [valid_positions, vocab_size]

        # Gather the log probabilities corresponding to the target labels
        # This selects the predicted probability for each true class
        target_log_probs = log_probs[range(log_probs.size(0)), labels_filtered]

        # Calculate negative log-likelihood (cross-entropy when using log_softmax)
        nll = -target_log_probs  # shape: [valid_positions]

        # Compute mean loss over all non-padding tokens
        loss = nll.mean()

        return loss


class CustomFocalLoss(nn.CrossEntropyLoss):
    def __init__(self, gamma=2, weights=None, device=None):
        super(CustomFocalLoss, self).__init__()
        self.weights = weights
        self.gamma = gamma
        self.device = device

    def forward(self, inputs, targets):
        batch_size, seq_len, vocab_size = inputs.shape

        # Flatten logits and labels
        logits_flat = inputs.view(-1, vocab_size)  # shape: [batch_size * seq_len, vocab_size]
        labels_flat = targets.view(-1)  # shape: [batch_size * seq_len]

        # Create mask to ignore padding tokens
        mask = labels_flat != -100  # shape: [batch_size * seq_len]

        # Filter out ignored positions
        logits_filtered = logits_flat[mask]  # shape: [valid_positions, vocab_size]
        labels_filtered = labels_flat[mask]  # shape: [valid_positions]

        probs = F.softmax(logits_filtered, dim=1)
        log_probs = F.log_softmax(logits_filtered, dim=-1)

        p_t = probs[torch.arange(probs.size(0)), labels_filtered]  # [N]
        log_p_t = log_probs[torch.arange(log_probs.size(0)), labels_filtered]

        # Apply focal loss formula
        modulating_factor = (1 - p_t) ** self.gamma  # [N]
        nll = -modulating_factor * log_p_t

        losses = torch.split(nll, inputs.shape[1])
        losses2 = []

        for idx in range(len(losses)):
            losses2.append(losses[idx].mean() * self.weights[idx])  #
        loss2 = torch.stack(losses2).mean()
        return loss2


class CustomAntiFocalLoss(nn.CrossEntropyLoss):
    def __init__(self, gamma=2, weights=None, device=None):
        super(CustomAntiFocalLoss, self).__init__()
        self.weights = weights
        self.gamma = gamma
        self.device = device

    def forward(self, inputs, targets):
        batch_size, seq_len, vocab_size = inputs.shape

        # Flatten logits and labels
        logits_flat = inputs.view(-1, vocab_size)  # shape: [batch_size * seq_len, vocab_size]
        labels_flat = targets.view(-1)  # shape: [batch_size * seq_len]

        # Create mask to ignore padding tokens
        mask = labels_flat != -100  # shape: [batch_size * seq_len]

        # Filter out ignored positions
        logits_filtered = logits_flat[mask]  # shape: [valid_positions, vocab_size]
        labels_filtered = labels_flat[mask]  # shape: [valid_positions]

        probs = F.softmax(logits_filtered, dim=1)
        log_probs = F.log_softmax(logits_filtered, dim=-1)

        p_t = probs[torch.arange(probs.size(0)), labels_filtered]  # [N]
        log_p_t = log_probs[torch.arange(log_probs.size(0)), labels_filtered]

        # Apply focal loss formula
        modulating_factor = (1 + p_t) ** self.gamma  # [N]
        nll = -modulating_factor * log_p_t

        losses = torch.split(nll, inputs.shape[1])
        losses2 = []

        for idx in range(len(losses)):
            losses2.append(losses[idx].mean() * self.weights[idx])  #
        loss2 = torch.stack(losses2).mean()
        return loss2


class CustomWeigthedLoss(nn.Module):
    def __init__(self, weights=None, device=None):
        super(CustomWeigthedLoss, self).__init__()
        self.weights = weights
        self.device = device

    def forward(self, inputs, targets):
        loss_fn = torch.nn.CrossEntropyLoss(ignore_index=-100, reduction="none")

        loss = loss_fn(inputs.view(-1, inputs.shape[-1]), targets.view(-1))
        losses = torch.split(loss, inputs.shape[1])
        losses2 = []

        for idx in range(len(losses)):
            losses2.append(losses[idx].mean() * self.weights[idx])
        loss2 = torch.stack(losses2).mean()
        return loss2

