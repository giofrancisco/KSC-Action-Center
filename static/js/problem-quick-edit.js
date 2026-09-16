document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById(
        "problemQuickEditModal"
    );

    if (!modal) {
        return;
    }

    const form = document.getElementById(
        "problemQuickEditForm"
    );

    const title = document.getElementById(
        "problemQuickEditModalLabel"
    );

    const assignedTo = document.getElementById(
        "quickAssignedTo"
    );

    const priority = document.getElementById(
        "quickPriority"
    );

    const status = document.getElementById(
        "quickStatus"
    );

    const dueAt = document.getElementById(
        "quickDueAt"
    );

    modal.addEventListener(
        "show.bs.modal",
        function (event) {
            const button = event.relatedTarget;

            if (!button) {
                return;
            }

            const problemId =
                button.dataset.problemId || "";

            const problemTitle =
                button.dataset.problemTitle || "";

            form.action =
                button.dataset.updateUrl || "";

            assignedTo.value =
                button.dataset.assignedTo || "";

            priority.value =
                button.dataset.priority || "P2";

            status.value =
                button.dataset.status || "NEW";

            dueAt.value =
                button.dataset.dueAt || "";

            title.textContent =
                problemId
                    ? `Editar atividade #${problemId} — ${problemTitle}`
                    : "Editar atividade";
        }
    );
});
