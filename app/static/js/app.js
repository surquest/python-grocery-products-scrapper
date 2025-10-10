        // Configuration
        const MOCK_MODE = false;
        const API_ENDPOINT = '/products:scrape';
        const DEFAULT_IMAGE_URL = 'https://via.placeholder.com/300x250?text=No+Image';
        const CURRENCY = 'Kč';

        const FALLBACK_IMAGE_SVG = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iI2UwZTBlMCI+PHBhdGggZD0iTTE5IDV2MTRINVYxOWgwbC44OC0xLjA2YTIgMiAwIDAgMSAyLjgyIDBsMi44MiAyLjgyYTIgMiAwIDAgMCAyLjgyIDBsMy45OC0zLjk4YTIgMiAwIDAgMSAyLjgyIDBMMTkgMTR2MWgtMVY1eiIvPjwvc3ZnPg==';

        const MOCK_RESPONSE = [{"id":"7890123","tpnb":"A1B2C3D4","title":"Premium Sparkling Water, Lemon & Lime Flavour","brandName":"Aqua Zest","price":38.90,"description":["A refreshing and crisp sparkling water perfect for summer refreshment. Naturally flavored with real fruit extracts. Low calorie and zero sugar."],"imageUrl":DEFAULT_IMAGE_URL,"superDepartmentName":"Beverages","departmentName":"Soft Drinks","shelfName":"Flavored Water"},{"id":"3456789","tpnb":"E5F6G7H8","title":"Dark Roast Coffee Beans, Single Origin Ethiopia","brandName":"Bean Enthusiast","price":199.50,"description":["Rich, dark roast with notes of chocolate and caramel. Sustainably sourced from high-altitude Ethiopian farms. Best consumed within 3 months of opening."],"imageUrl":'https://images.unsplash.com/photo-1517404215738-15263e9f4a54?w=300&h=300&fit=crop&q=80',"superDepartmentName":"Pantry","departmentName":"Hot Drinks","shelfName":"Coffee"},{"id":"101112","tpnb":"I9J0K1L2","title":"Organic Whole Wheat Bread Loaf (Missing Image Test)","brandName":"Bakers Delight","price":45.00,"description":["A hearty whole wheat loaf baked fresh daily. Great source of fiber. This description is intentionally very long to test truncation functionality. The quick brown fox jumps over the lazy dog and then takes a nap under the sun."],"imageUrl":'http://nonexistent-url.com/image.jpg',"superDepartmentName":"Bakery","departmentName":"Bread","shelfName":"Loaves"}];

        // DOM Elements
        const inputEl = document.getElementById('product-input');
        const scrapeBtn = document.getElementById('scrape-btn');
        const clearBtn = document.getElementById('clear-btn');
        const statusEl = document.getElementById('status-message');
        const resultsContainer = document.getElementById('results-container');
        const mainContent = document.getElementById('main-content');
        const spinner = scrapeBtn.querySelector('md-circular-progress');
        const countrySelectEl = document.getElementById('country-select'); // New element

        // State
        let productCache = {};

        // Utility Functions
        function truncateText(text, maxLength = 120) {
            return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
        }

        function setStatus(message, type = 'info') {
            statusEl.innerHTML = message;
            statusEl.className = `status-${type}`;
            statusEl.style.display = 'block';
        }

        function clearStatus() {
            statusEl.textContent = '';
            statusEl.className = '';
            statusEl.style.display = 'none';
        }

        function setLoading(isLoading) {
            scrapeBtn.disabled = isLoading;
            clearBtn.disabled = isLoading;
            scrapeBtn.classList.toggle('loading', isLoading);
            if(spinner) spinner.style.display = isLoading ? 'block' : 'none';
            mainContent.setAttribute('aria-busy', isLoading);
        }

        function processInput(rawText) {
            return rawText.split('\n').map(line => line.trim()).filter(line => line.length > 0);
        }

        // Card Rendering
        function createCard(product) {
            const getMetadata = (p) => [p.superDepartmentName, p.departmentName, p.shelfName].filter(Boolean).join(' › ');
            
            const descriptionText = Array.isArray(product.description) && product.description.length > 0 
                ? product.description[0] 
                : 'No description provided.';

            const card = document.createElement('div');
            card.className = 'product-card';
            card.innerHTML = `
                <md-elevation></md-elevation>
                <div class="card-image-container">
                    <img src="${product.defaultImageUrl || DEFAULT_IMAGE_URL}" 
                         alt="Image of ${product.title}" 
                         loading="lazy" 
                         onerror="this.onerror=null; this.src='${FALLBACK_IMAGE_SVG}';">
                </div>
                <div class="card-content">
                    <p class="card-brand">${product.brandName || 'Unknown Brand'}</p>
                    <h3 class="card-title">${product.title || 'Untitled Product'}</h3>
                    <p class="card-price">${(product.price || 0).toFixed(2)} ${CURRENCY}</p>
                    <p class="card-description">${truncateText(descriptionText)}</p>
                    <p class="card-metadata">${getMetadata(product)}</p>
                </div>
            `;
            return card;
        }

        function renderResults(products, errors=[]) {
            resultsContainer.innerHTML = '';
            if (!products || products.length === 0) {
                setStatus('No products found matching the input criteria.', 'error');
                return;
            }
            if (errors.length > 0) {
                // Define chip-set for first 3 errors
                const chipSet = document.createElement('md-chip-set');
                // Add each error as an assist chip
                errors.slice(0, 3).forEach(error => {
                    const chip = document.createElement('md-assist-chip');
                    chip.setAttribute('label', error);
                    chipSet.appendChild(chip);
                });

                setStatus(`<p>These ${errors.length} products was not found: ${chipSet.outerHTML} and probably 
                more ... </p>`, 'warning');
            } else {
                setStatus(`Successfully loaded ${products.length} product(s).`, 'success');
            }
            products.forEach(product => resultsContainer.appendChild(createCard(product)));
        }

        // Main Event Handlers
        async function handleScrape() {
            clearStatus();
            resultsContainer.innerHTML = '';
            setLoading(true);

            const lines = processInput(inputEl.value);
            const selectedCountry = countrySelectEl.value; // Get selected country
            const inputKey = `${selectedCountry}|${lines.join('|')}`; // Make cache key country-specific

            if (lines.length === 0) {
                setStatus('Please paste at least one product ID.', 'error');
                setLoading(false);
                return;
            }
            
            if (productCache[inputKey]) {
                renderResults(productCache[inputKey]);
                setLoading(false);
                return;
            }

            try {
                let data;
                if (MOCK_MODE) {
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    data = {"products": MOCK_RESPONSE};
                } else {
                    setStatus(`Sending request for country: ${selectedCountry.toUpperCase()}...`, 'info');
                    // Append country to the API endpoint as a query parameter
                    const urlWithQuery = `${API_ENDPOINT}?country=${selectedCountry}`;
                    
                    const response = await fetch(urlWithQuery, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(lines)
                    });
                    if (!response.ok) {
                        const errorBody = await response.json().catch(() => ({ message: `HTTP Error ${response.status}` }));
                        throw new Error(errorBody.message || `Request failed with status ${response.status}`);
                    }
                    data = await response.json();
                }

                if (!Array.isArray(data.products)) {
                    throw new Error('Invalid data format received from server.');
                }

                productCache[inputKey] = data.products;
                renderResults(data.products, data.errors);

            } catch (error) {
                console.error('Scrape Operation Failed:', error);
                setStatus(`Error: ${error.message || 'A network error occurred.'}`, 'error');
            } finally {
                setLoading(false);
            }
        }

        function handleClear() {
            inputEl.value = '';
            resultsContainer.innerHTML = '';
            clearStatus();
            mainContent.setAttribute('aria-busy', false);
        }

        // Event Listeners
        scrapeBtn.addEventListener('click', handleScrape);
        clearBtn.addEventListener('click', handleClear);
        
        inputEl.addEventListener('keyup', (e) => {
            if ((e.key === 'Enter' && (e.ctrlKey || e.metaKey)) && !scrapeBtn.disabled) {
                handleScrape();
            }
        });

        document.addEventListener('DOMContentLoaded', () => {
            if (MOCK_MODE) {
                setStatus('Application running in MOCK MODE.', 'info');
            }
        });