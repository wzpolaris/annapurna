# Example Markdown Drawer

This drawer is written in **pure Markdown** (.md file)!

## Features

- Simple Markdown syntax
- Full KaTeX math support: $E = mc^2$
- Code blocks with syntax highlighting
- Tables, lists, blockquotes
- Links and images

## Code Example

```python
def calculate_returns(prices):
    """Calculate periodic returns from price series."""
    returns = prices.pct_change()
    return returns.dropna()
```

## Math Support

Inline math: The variance is $\sigma^2 = \frac{1}{N}\sum_{i=1}^{N}(x_i - \mu)^2$

Display math:

$$
r_t = \alpha + \beta r_{t-1} + \epsilon_t
$$

## Lists

### Ordered
1. First step
2. Second step
3. Third step

### Unordered
- Bullet point one
- Bullet point two
- Bullet point three

## Tables

| Feature | HTML | Markdown |
|---------|------|----------|
| Ease of writing | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Styling control | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Math support | ✓ | ✓ |

## Blockquote

> **Note**: This drawer is automatically converted from Markdown to HTML by the backend with full KaTeX and styling support!

---

You can now write drawers in simple Markdown instead of HTML!
