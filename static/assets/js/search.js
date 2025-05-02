// static/js/search.js

$(document).ready(function () {
    // Trigger the search function when the input field is focused or typed into
    $("#search-box").on("focus keyup", function () {
        let query = $(this).val().trim();

        // Only run the AJAX call if the input has at least 1 character (if desired)
        if (query.length > 1) {
            $.ajax({
                url: "{% url 'employees:global_search' %}",  // Ensure this URL points to the correct endpoint
                data: { "q": query },
                dataType: "json",
                success: function (data) {
                    // Log the response data to the console
                    console.log(data);

                    let resultsBox = $("#search-results");
                    resultsBox.empty(); // Clear previous results

                    // Clear the fallback message
                    $(".fallback").addClass("d-none");

                    // Show the search results container
                    $("#search-dropdown").show();

                    // Employees section
                    if (data.employees.length) {
                        resultsBox.append("<h6 class='dropdown-header text-body-highlight fs-9 border-bottom border-translucent py-2 lh-sm'>Сотрудники</h6>");
                        data.employees.forEach(emp => {
                            resultsBox.append(`
                            <div class="py-2">
                                <a class="dropdown-item py-2 d-flex align-items-center" href="/employee/${emp.id}/">
                                    <div class="flex-1">
                                        <h6 class="mb-0 text-body title">${emp.first_name} ${emp.last_name} - ${emp.plant}</h6>
                                    </div>
                                </a>
                            </div>
                        `);
                        });
                    }

                    // If no results found
                    if (!data.employees.length) {
                        $(".fallback").removeClass("d-none");
                    }
                }
            });
        } else {
            // Clear the search results if query length is less than 2 characters
            $("#search-results").empty();
            $(".fallback").addClass("d-none");
            $("#search-dropdown").hide(); // Hide the dropdown if no input
        }
    });

    // Hide dropdown when clicking outside of the search box or the results
    $(document).on("click", function (e) {
        if (!$(e.target).closest("#search-box, #search-dropdown").length) {
            $("#search-dropdown").hide(); // Hide dropdown on click outside
        }
    });
});
