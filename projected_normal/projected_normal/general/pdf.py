"""Probability density function (PDF) for the general projected normal distribution."""
import torch


__all__ = ["pdf", "log_pdf"]


def __dir__():
    return __all__


def pdf(mu, covariance, y):
    """
    Compute the probability density function of a projected Gaussian distribution with parameters mu and covariance at points y.

    Parameters
    ----------------
      - mu : Mean of the non-projected Gaussian. Shape (n_dim).
      - covariance : Covariance matrix of the non-projected Gaussian. Shape (n_dim x n_dim).
      - y : Points where to evaluate the PDF. Shape (n_points x n_dim).

    Returns
    ----------------
      - PDF evaluated at y. Shape (n_points).
    """
    lpdf = log_pdf(mu, covariance, y)
    pdf = torch.exp(lpdf)
    return pdf


def log_pdf(mu, covariance, y):
    """
    Compute the log probability density function of a projected
    normal distribution with parameters mu and covariance.

    Parameters
    ----------------
      - mu : Mean of the non-projected Gaussian. Shape (n_dim).
      - covariance : Covariance matrix of the non-projected Gaussian. Shape (n_dim x n_dim).
      - y : Points where to evaluate the PDF. Shape (n_points x n_dim).

    Returns
    ----------------
      log-PDF evaluated at y. Shape (n_points).
    """
    n_dim = torch.tensor(mu.size(0))
    # Compute the precision matrix
    precision = torch.linalg.inv(covariance)

    # Compute the terms
    q1 = torch.einsum("i,ij,j->", mu, precision, mu)
    q2 = torch.einsum("i,ij,j...->...", mu, precision, y.t())
    q3 = torch.einsum("...i,ij,j...->...", y, precision, y.t())
    alpha = q2 / torch.sqrt(q3)
    M = _M_value(alpha, n_dim=n_dim)

    # Compute the log PDF
    term1 = -(n_dim / 2.0) * torch.log(torch.tensor(2.0) * torch.pi)
    term2 = -0.5 * torch.logdet(covariance)
    term3 = -(n_dim / 2.0) * torch.log(q3)
    term4 = 0.5 * (alpha**2 - q1)
    term5 = torch.log(M)
    lpdf = term1 + term2 + term3 + term4 + term5
    return lpdf


def _M_value(alpha, n_dim):
    """
    Compute value of recursive function M in the projected normal pdf, with input alpha.

    Parameters
    ----------------
      - alpha : Input to function M (n).
      - n_dim : Dimension of the non-projected Gaussian.

    Returns
    ----------------
      Value of M(alpha) (n).
    """
    # Create a standard normal distribution
    normal_dist = torch.distributions.Normal(0, 1)
    # Calculate the cumulative distribution function (CDF) of alpha
    norm_cdf = normal_dist.cdf(alpha)

    # Calculate unnormalized pdf
    exp_alpha = torch.exp(-0.5 * alpha**2)

    # Calculate the value of M recursively
    # List with values to modify iteratively
    M1 = torch.sqrt(torch.tensor(2.0) * torch.pi) * norm_cdf
    M2 = exp_alpha + alpha * M1
    M_vals = [M1, M2]
    for i in range(3, n_dim + 1):
        M_next = (i - 2) * M_vals[0] + alpha * M_vals[1]
        M_vals[0] = M_vals[1].clone()
        M_vals[1] = M_next.clone()

    return M_vals[1]

