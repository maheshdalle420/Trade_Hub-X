// Auction Timer Functionality
function updateTimer(endTime, elementId) {
    const timerElement = document.getElementById(elementId);

    const timer = setInterval(() => {
        const now = new Date().getTime();
        const end = new Date(endTime).getTime();
        const distance = end - now;

        if (distance > 0) {
            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            timerElement.innerHTML = `<span class="timer-text">${days}d ${hours}h ${minutes}m ${seconds}s</span>`;
        } else {
            clearInterval(timer);
            timerElement.innerHTML = `<span class="auction-ended">AUCTION ENDED</span>`;
            handleAuctionEnd(elementId);
        }
    }, 1000);
}

// Place Bid with Updated Notifications and Styling
async function placeBid(auctionId) {
    const bidAmount = document.getElementById(`bid-amount-${auctionId}`).value.trim();
    if (!bidAmount || isNaN(bidAmount)) {
        showNotification('Please enter a valid bid amount.', 'error');
        return;
    }

    try {
        const response = await fetch('/api/place-bid', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ auction_id: auctionId, bid_amount: bidAmount })
        });

        const data = await response.json();
        if (data.success) {
            showNotification('Bid placed successfully!', 'success');
            updateBidDisplay(auctionId, bidAmount);
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error placing bid. Please try again.', 'error');
    }
}

// Update Bidding Display
function updateBidDisplay(auctionId, bidAmount) {
    const bidElement = document.getElementById(`current-bid-${auctionId}`);
    if (bidElement) {
        bidElement.textContent = `Current Bid: $${bidAmount}`;
    }
}

// Notification System with Updated Styles
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `<span>${message}</span>`;

    document.body.appendChild(notification);
    setTimeout(() => { notification.remove(); }, 3000);
}

// Wishlist Toggle Integration
async function toggleWishlist(propertyId) {
    const wishlistBtn = document.getElementById(`wishlist-${propertyId}`);
    try {
        const response = await fetch('/api/toggle-wishlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ property_id: propertyId })
        });

        const data = await response.json();
        wishlistBtn.classList.toggle('active');
        showNotification(data.message, 'success');
    } catch (error) {
        showNotification('Failed to update wishlist.', 'error');
    }
}

// Real-time Bid Updates with WebSocket Integration
let socket;
function initializeWebSocket() {
    socket = new WebSocket(`wss://${window.location.host}/ws/auctions`);

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'bid_update') {
            updateBidDisplay(data.auction_id, data.new_bid);
            if (data.outbid) {
                showNotification('You have been outbid!', 'warning');
            }
        } else if (data.type === 'auction_end') {
            handleAuctionEnd(data.auction_id);
        }
    };

    socket.onclose = () => {
        setTimeout(initializeWebSocket, 5000); // Reconnect on disconnect
    };
}

// Handle Auction End
function handleAuctionEnd(auctionId) {
    const auctionElement = document.getElementById(`auction-${auctionId}`);
    if (auctionElement) {
        auctionElement.innerHTML += `<div class="auction-ended">Auction Ended</div>`;
    }
}

// Property Search Initialization
function initializeSearch() {
    const searchForm = document.getElementById('property-search');
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const searchParams = new URLSearchParams(new FormData(searchForm));
        const resultsContainer = document.getElementById('search-results');

        try {
            const response = await fetch(`/api/search?${searchParams}`);
            const data = await response.json();
            resultsContainer.innerHTML = renderSearchResults(data.results);
        } catch (error) {
            showNotification('Search failed. Please try again.', 'error');
        }
    });
}

function renderSearchResults(results) {
    if (!results.length) return '<p>No results found.</p>';
    return results.map(item => `
        <div class="search-result">
            <h3>${item.title}</h3>
            <p>${item.description}</p>
        </div>
    `).join('');
}

// Initialize WebSocket and Search on Load
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    initializeSearch();
});



// Property Search Functionality
function initializeSearch() {
    const searchForm = document.getElementById('property-search');
    const resultsContainer = document.getElementById('search-results');

    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Collect form data
        const formData = new FormData(searchForm);
        const searchParams = new URLSearchParams(formData);

        // Clear previous results
        resultsContainer.innerHTML = '<p>Loading...</p>';

        try {
            // Fetch search results
            const response = await fetch(`/api/search?${searchParams}`);
            const data = await response.json();

            if (data.results.length > 0) {
                resultsContainer.innerHTML = renderSearchResults(data.results);
            } else {
                resultsContainer.innerHTML = '<p>No results found.</p>';
            }
        } catch (error) {
            resultsContainer.innerHTML = '<p>Error fetching search results. Please try again.</p>';
            console.error('Search error:', error);
        }
    });
}

// Render Search Results
function renderSearchResults(results) {
    return results
        .map(
            (result) => `
            <div class="search-result">
                <h3>${result.title}</h3>
                <p>${result.description}</p>
                <p class="price">$${result.price}</p>
            </div>
        `
        )
        .join('');
}



// Remove Item from Wishlist
async function removeFromWishlist(wishlistId) {
    try {
        const response = await fetch(`/api/remove-wishlist/${wishlistId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
        });
        const data = await response.json();

        if (data.success) {
            document.getElementById(`wishlist-${wishlistId}`).remove();
            showNotification('Item removed from wishlist.', 'success');
        } else {
            showNotification('Error removing item.', 'error');
        }
    } catch (error) {
        showNotification('An error occurred. Please try again.', 'error');
        console.error(error);
    }
}

// View Auction
function viewAuction(auctionId) {
    window.location.href = `/auction/${auctionId}`;
}


// Approve Listing
async function approveListing(listingId) {
    try {
        const response = await fetch(`/api/approve-listing/${listingId}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            document.getElementById(`listing-${listingId}`).remove();
            showNotification('Listing approved successfully!', 'success');
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error approving listing.', 'error');
    }
}

// Reject Listing
async function rejectListing(listingId) {
    try {
        const response = await fetch(`/api/reject-listing/${listingId}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            document.getElementById(`listing-${listingId}`).remove();
            showNotification('Listing rejected successfully!', 'success');
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error rejecting listing.', 'error');
    }
}

// Toggle User Status
async function toggleUserStatus(userId) {
    try {
        const response = await fetch(`/api/toggle-user-status/${userId}`, { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            const statusCell = document.querySelector(`#user-${userId} .user-status`);
            statusCell.textContent = data.new_status;
            showNotification('User status updated.', 'success');
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error updating user status.', 'error');
    }
}

// Delete User
async function deleteUser(userId) {
    try {
        const response = await fetch(`/api/delete-user/${userId}`, { method: 'DELETE' });
        const data = await response.json();
        if (data.success) {
            document.getElementById(`user-${userId}`).remove();
            showNotification('User deleted successfully.', 'success');
        } else {
            showNotification(data.message, 'error');
        }
    } catch (error) {
        showNotification('Error deleting user.', 'error');
    }
}
