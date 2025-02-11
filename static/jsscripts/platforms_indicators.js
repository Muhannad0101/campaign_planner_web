document.addEventListener('DOMContentLoaded', function () {
    const platformSelect = document.getElementById('platform_name');
    const indicatorsContainer = document.getElementById('indicators-container');
    const addedPlatformsList = document.getElementById('added-platforms-list');

    // Check if platformSelect exists before adding event listener
    if (platformSelect) {
        platformSelect.addEventListener('change', function () {
            const selectedPlatform = this.value;
            if (!selectedPlatform) {
                indicatorsContainer.innerHTML = '';
                return;
            }

            // Fetch indicators from pricingTable (passed as JSON)
            const pricingTable = window.pricingTable || [];
            const platformData = pricingTable.filter(item => item['channel'] === selectedPlatform);
            const indicators = platformData.map(item => item['indicator']).filter(ind => ind);

            let html = '';
            indicators.forEach(indicator => {
                html += `
                    <div class="mb-3">
                        <label for="input_method_${selectedPlatform}_${indicator}" class="form-label">
                            اختر طريقة الإدخال (العدد المستهدف أو السعر الإجمالي) لمؤشر "${indicator}"
                        </label>
                        <select name="input_method_${selectedPlatform}_${indicator}" id="input_method_${selectedPlatform}_${indicator}" class="form-select">
                            <option value="" selected disabled>اختر طريقة الإدخال</option>
                            <option value="target">أدخل المستهدف</option>
                            <option value="total_price">أدخل السعر الإجمالي</option>
                        </select>
                    </div>

                    <div class="mb-3" id="value_field_${selectedPlatform}_${indicator}" style="display: none;">
                        <label for="value_${selectedPlatform}_${indicator}" class="form-label">
                            أدخل القيمة لمؤشر "${indicator}"
                        </label>
                        <input type="number" step="any" name="value_${selectedPlatform}_${indicator}" id="value_${selectedPlatform}_${indicator}" class="form-control" placeholder="أدخل القيمة هنا">
                    </div>
                `;
            });

            indicatorsContainer.innerHTML = html;

            // Attach event listeners to the new select fields
            indicators.forEach(indicator => {
                const select = document.getElementById(`input_method_${selectedPlatform}_${indicator}`);
                const valueFieldDiv = document.getElementById(`value_field_${selectedPlatform}_${indicator}`);
                const valueInput = document.getElementById(`value_${selectedPlatform}_${indicator}`);

                if (select && valueFieldDiv && valueInput) {
                    select.addEventListener('change', function () {
                        if (this.value === 'target' || this.value === 'total_price') {
                            valueFieldDiv.style.display = 'block';
                            valueInput.required = true;
                        } else {
                            valueFieldDiv.style.display = 'none';
                            valueInput.required = false;
                            valueInput.value = '';
                        }
                    });
                } else {
                    console.error(`One or more elements for indicator "${indicator}" not found.`);
                }
            });
        });
    } else {
        console.warn('Element with ID "platform_name" not found. Skipping platformSelect event listener.');
    }

    // Handle removal of platforms
    if (addedPlatformsList) {
        addedPlatformsList.addEventListener('click', function (e) {
            if (e.target && e.target.classList.contains('remove-platform')) {
                const platformName = e.target.getAttribute('data-platform');

                if (confirm(`هل أنت متأكد أنك تريد إزالة منصة "${platformName}"؟`)) {
                    // Ensure removePlatformUrl and csrfToken are defined
                    if (window.removePlatformUrl && window.csrfToken) {
                        // Send AJAX request to remove the platform
                        fetch(window.removePlatformUrl, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': window.csrfToken
                            },
                            body: JSON.stringify({ 'platform_name': platformName })
                        })
                            .then(response => response.json())
                            .then(data => {
                                if (data.status === 'success') {
                                    // Remove the platform from the DOM
                                    const listItem = e.target.closest('li');
                                    if (listItem) {
                                        listItem.remove();
                                    }
                                    // Optionally, display a success message
                                    showAlert(data.message, 'success');
                                } else {
                                    // Optionally, display an error message
                                    showAlert(data.message, 'danger');
                                }
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                showAlert('حدث خطأ أثناء إزالة المنصة.', 'danger');
                            });
                    } else {
                        console.error('removePlatformUrl or csrfToken is not defined.');
                        showAlert('حدث خطأ في الإعدادات.', 'danger');
                    }
                }
            }
        });
    }

    // Function to display alerts dynamically
    function showAlert(message, category) {
        const container = document.querySelector('.container');
        if (!container) {
            console.error('Container element not found for alerts.');
            return;
        }

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${category} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        container.insertBefore(alertDiv, container.firstChild);
    }
});
