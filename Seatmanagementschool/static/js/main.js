/* Client-side helper scripts for School Seat Management System */

document.addEventListener('DOMContentLoaded', function() {
    // Student Table Search
    const searchInput = document.getElementById('studentSearch');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const query = this.value.toLowerCase();
            const rows = document.querySelectorAll('#studentsTableBody tr');
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }

    // Class/Block Filter in Students Page
    const filterBlock = document.getElementById('filterBlock');
    const filterClass = document.getElementById('filterClass');
    if (filterBlock || filterClass) {
        const applyFilters = () => {
            const blockVal = filterBlock ? filterBlock.value : '';
            const classVal = filterClass ? filterClass.value : '';
            const rows = document.querySelectorAll('#studentsTableBody tr');
            
            rows.forEach(row => {
                const rowBlock = row.getAttribute('data-block') || '';
                const rowClass = row.getAttribute('data-class') || '';
                
                const matchBlock = !blockVal || rowBlock === blockVal;
                const matchClass = !classVal || rowClass === classVal;
                
                row.style.display = (matchBlock && matchClass) ? '' : 'none';
            });
        };

        if (filterBlock) filterBlock.addEventListener('change', applyFilters);
        if (filterClass) filterClass.addEventListener('change', applyFilters);
    }
});

// Modal Helpers
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Close modal when clicking outside content
window.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});
