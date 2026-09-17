document.addEventListener(
    "DOMContentLoaded",
    function () {

        const modal =
            document.getElementById(
                "wsusTaskModal"
            );

        if (!modal) {
            return;
        }

        const form =
            document.getElementById(
                "wsusTaskForm"
            );

        const title =
            document.getElementById(
                "wsusTaskModalLabel"
            );

        const computerInfo =
            document.getElementById(
                "wsusTaskComputerInfo"
            );

        const assignedTo =
            document.getElementById(
                "wsusTaskAssignedTo"
            );

        const priority =
            document.getElementById(
                "wsusTaskPriority"
            );

        const status =
            document.getElementById(
                "wsusTaskStatus"
            );

        const startAt =
            document.getElementById(
                "wsusTaskStartAt"
            );

        const endAt =
            document.getElementById(
                "wsusTaskEndAt"
            );

        const allowReboot =
            document.getElementById(
                "wsusTaskAllowReboot"
            );

        const notes =
            document.getElementById(
                "wsusTaskNotes"
            );

        const submitButton =
            document.getElementById(
                "wsusTaskSubmitButton"
            );


        modal.addEventListener(
            "show.bs.modal",
            function (event) {

                const button =
                    event.relatedTarget;

                if (!button) {
                    return;
                }

                const mode =
                    button.dataset.mode
                    || "create";

                form.action =
                    button.dataset.actionUrl
                    || "";

                assignedTo.value =
                    button.dataset.assignedTo
                    || "";

                priority.value =
                    button.dataset.priority
                    || "P2";

                status.value =
                    button.dataset.status
                    || "PENDING";

                startAt.value =
                    button.dataset.startAt
                    || "";

                endAt.value =
                    button.dataset.endAt
                    || "";

                allowReboot.checked =
                    button.dataset.allowReboot
                    === "1";

                notes.value =
                    button.dataset.notes
                    || "";

                const hostname =
                    button.dataset.hostname
                    || "";

                const ip =
                    button.dataset.ip
                    || "";

                if (mode === "edit") {

                    const taskId =
                        button.dataset.taskId
                        || "";

                    title.textContent =
                        `Editar atividade #${taskId}`;

                    submitButton.textContent =
                        "Salvar alterações";

                }
                else {

                    title.textContent =
                        "Nova atividade WSUS";

                    submitButton.textContent =
                        "Criar atividade";

                }

                computerInfo.textContent =
                    (
                        ip
                        ? `${hostname} • ${ip}`
                        : hostname
                    );

            }
        );


        modal.addEventListener(
            "hidden.bs.modal",
            function () {

                form.action = "";

                assignedTo.value = "";

                priority.value = "P2";

                status.value = "PENDING";

                startAt.value = "";

                endAt.value = "";

                allowReboot.checked = false;

                notes.value = "";

                computerInfo.textContent = "";

            }
        );

    }
);
