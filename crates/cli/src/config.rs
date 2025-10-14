use etcetera::AppStrategyArgs;
use once_cell::sync::Lazy;

/// Application strategy configuration for determining config directory paths
pub static APP_STRATEGY: Lazy<AppStrategyArgs> = Lazy::new(|| AppStrategyArgs {
    top_level_domain: "Red Hat".to_string(),
    author: "Lightspeed".to_string(),
    app_name: "cli".to_string(),
});

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_app_strategy_initialization() {
        // Test that the lazy static initializes correctly
        let strategy = &*APP_STRATEGY;

        assert_eq!(strategy.top_level_domain, "Red Hat");
        assert_eq!(strategy.author, "Lightspeed");
        assert_eq!(strategy.app_name, "cli");
    }

    #[test]
    fn test_app_strategy_is_immutable() {
        // Access multiple times to ensure it's consistently the same
        let strategy1 = &*APP_STRATEGY;
        let strategy2 = &*APP_STRATEGY;

        assert_eq!(strategy1.app_name, strategy2.app_name);
        assert_eq!(strategy1.author, strategy2.author);
        assert_eq!(strategy1.top_level_domain, strategy2.top_level_domain);
    }
}
