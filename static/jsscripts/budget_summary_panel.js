document.addEventListener('DOMContentLoaded', function () {
    const surplusElement = document.getElementById('surplus-value');
    const budgetElement = document.getElementById('budget-value');
    const totalCostElement = document.getElementById('total-cost-value');
    const vatElement = document.getElementById('vat-value');
    const managementFeesElement = document.getElementById('management-fees-value');
    const managementFeePercentageElement = document.getElementById('management-fee-percentage');
    const grandTotalElement = document.getElementById('grand-total-value');
    
    // Existing Financial Elements
    // const platformsCostElement = document.getElementById('platforms-cost');
    // const optionalServicesCostElement = document.getElementById('optional-services-cost');
    // const influencersCostElement = document.getElementById('influencers-cost');
    // const newsAccountsCostElement = document.getElementById('news-accounts-cost');

    // New Financial Elements
    // const miscellaneousCostElement = document.getElementById('miscellaneous-cost');
    // const contingencyFundElement = document.getElementById('contingency-fund');
    // const platformFeesElement = document.getElementById('platform-fees');
    // const advertisingFeesElement = document.getElementById('advertising-fees');

    // Use the global variable set in the HTML
    const getCampaignSummaryUrl = window.getCampaignSummaryUrl;

    function updateSummary() {
        // If budget summary isn't present (like on index), do nothing
        if (!surplusElement) return;

        fetch(getCampaignSummaryUrl)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.warn(data.error);
                    return;
                }

                console.log('Surplus Value:', data.surplus);
                console.log('Type of Surplus:', typeof data.surplus);

                const surplus = parseFloat(data.surplus);

                // Handle NaN cases
                if (isNaN(surplus)) {
                    console.warn('Surplus is not a number:', data.surplus);
                    surplusElement.textContent = 'N/A';
                    surplusElement.style.color = 'inherit';
                } else {
                    surplusElement.textContent = surplus.toLocaleString();

                    // Change color based on surplus value
                    if (surplus < 0) {
                        surplusElement.style.color = 'red';
                    } else {
                        surplusElement.style.color = 'inherit';
                    }
                }

                budgetElement.textContent = data.budget_expected.toLocaleString();
                totalCostElement.textContent = data.total_cost_excl_tax.toLocaleString();
                surplusElement.textContent = data.surplus.toLocaleString();
                vatElement.textContent = data.vat.toLocaleString();
                managementFeesElement.textContent = data.management_fees.toLocaleString();
                managementFeePercentageElement.textContent = data.management_fee_percentage.toLocaleString();
                grandTotalElement.textContent = data.grand_total.toLocaleString();

                // Update existing financial accounts
                // platformsCostElement.textContent = data.platforms_cost.toLocaleString();
                // optionalServicesCostElement.textContent = data.optional_services_cost.toLocaleString();
                // influencersCostElement.textContent = data.influencers_cost.toLocaleString();
                // newsAccountsCostElement.textContent = data.news_accounts_cost.toLocaleString();

                // new financial accounts
                // miscellaneousCostElement.textContent = data.miscellaneous_cost.toLocaleString();
                // contingencyFundElement.textContent = data.contingency_fund.toLocaleString();
                // platformFeesElement.textContent = data.platform_fees.toLocaleString();
                // advertisingFeesElement.textContent = data.advertising_fees.toLocaleString();

                // Change surplus color if negative
            })
            .catch(err => console.error('Error:', err));
    }

    // Add event listeners to inputs and selects to trigger updateSummary on change
    document.querySelectorAll('input, select').forEach(el => {
        el.addEventListener('change', updateSummary);
    });

    // Initial load
    updateSummary();
});