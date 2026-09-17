document.addEventListener(
    "DOMContentLoaded",
    function () {

        const modal =
            document.getElementById(
                "wsusTaskHistoryModal"
            );

        if (!modal) {
            return;
        }


        const loading =
            document.getElementById(
                "wsusHistoryLoading"
            );

        const error =
            document.getElementById(
                "wsusHistoryError"
            );

        const content =
            document.getElementById(
                "wsusHistoryContent"
            );

        const empty =
            document.getElementById(
                "wsusHistoryEmpty"
            );

        const timeline =
            document.getElementById(
                "wsusHistoryTimeline"
            );

        const title =
            document.getElementById(
                "wsusTaskHistoryModalLabel"
            );

        const computerInfo =
            document.getElementById(
                "wsusHistoryComputerInfo"
            );

        const priority =
            document.getElementById(
                "wsusHistoryPriority"
            );

        const status =
            document.getElementById(
                "wsusHistoryStatus"
            );

        const assignedTo =
            document.getElementById(
                "wsusHistoryAssignedTo"
            );

        const reboot =
            document.getElementById(
                "wsusHistoryReboot"
            );

        const startAt =
            document.getElementById(
                "wsusHistoryStartAt"
            );

        const endAt =
            document.getElementById(
                "wsusHistoryEndAt"
            );

        const notesBlock =
            document.getElementById(
                "wsusHistoryNotesBlock"
            );

        const notes =
            document.getElementById(
                "wsusHistoryNotes"
            );


        function resetModal() {

            loading.classList.remove(
                "d-none"
            );

            error.classList.add(
                "d-none"
            );

            content.classList.add(
                "d-none"
            );

            empty.classList.add(
                "d-none"
            );

            timeline.replaceChildren();

            title.textContent =
                "Histórico da atividade";

            computerInfo.textContent = "";

            priority.textContent = "";

            status.textContent = "";

            assignedTo.textContent = "";

            reboot.textContent = "";

            startAt.textContent = "";

            endAt.textContent = "";

            notes.textContent = "";

            notesBlock.classList.add(
                "d-none"
            );

        }


        function createEventElement(
            eventItem
        ) {

            const item =
                document.createElement(
                    "div"
                );

            item.className =
                "wsus-history-event";


            const rail =
                document.createElement(
                    "div"
                );

            rail.className =
                "wsus-history-event-rail";


            const marker =
                document.createElement(
                    "span"
                );

            marker.className =
                (
                    "wsus-history-event-marker "
                    +
                    `tone-${eventItem.tone || "secondary"}`
                );


            rail.appendChild(
                marker
            );


            const body =
                document.createElement(
                    "div"
                );

            body.className =
                "wsus-history-event-body";


            const header =
                document.createElement(
                    "div"
                );

            header.className =
                "wsus-history-event-header";


            const label =
                document.createElement(
                    "div"
                );

            label.className =
                "wsus-history-event-label";

            label.textContent =
                eventItem.label
                || eventItem.type
                || "Evento";


            const date =
                document.createElement(
                    "div"
                );

            date.className =
                "wsus-history-event-date";

            date.textContent =
                eventItem.created_at
                || "";


            header.appendChild(
                label
            );

            header.appendChild(
                date
            );


            const description =
                document.createElement(
                    "div"
                );

            description.className =
                "wsus-history-event-description";

            description.textContent =
                eventItem.description
                || "";


            const actor =
                document.createElement(
                    "div"
                );

            actor.className =
                "wsus-history-event-actor";

            actor.textContent =
                (
                    `Por: ${
                        eventItem.actor
                        || "Sistema"
                    }`
                );


            body.appendChild(
                header
            );

            body.appendChild(
                description
            );

            body.appendChild(
                actor
            );


            item.appendChild(
                rail
            );

            item.appendChild(
                body
            );


            return item;
        }


        async function loadHistory(
            historyUrl
        ) {

            try {

                const response =
                    await fetch(
                        historyUrl,
                        {
                            headers: {
                                "X-Requested-With":
                                    "XMLHttpRequest"
                            }
                        }
                    );


                const payload =
                    await response.json();


                if (
                    !response.ok
                    ||
                    !payload.ok
                ) {

                    throw new Error(
                        "Não foi possível carregar o histórico."
                    );

                }


                const task =
                    payload.task
                    || {};


                title.textContent =
                    (
                        `Histórico da atividade #${
                            task.id
                            || ""
                        }`
                    );


                computerInfo.textContent =
                    (
                        task.ip
                        ? `${task.hostname} • ${task.ip}`
                        : (
                            task.hostname
                            || ""
                        )
                    );


                priority.textContent =
                    task.priority
                    || "—";


                status.textContent =
                    task.status
                    || "—";


                assignedTo.textContent =
                    task.assigned_to
                    || "Não atribuído";


                reboot.textContent =
                    task.allow_reboot
                    ? "Sim"
                    : "Não";


                startAt.textContent =
                    task.planned_start_at
                    || "Não definido";


                endAt.textContent =
                    task.planned_end_at
                    || "Não definido";


                if (
                    task.notes
                    &&
                    task.notes.trim()
                ) {

                    notes.textContent =
                        task.notes;

                    notesBlock.classList.remove(
                        "d-none"
                    );

                }
                else {

                    notesBlock.classList.add(
                        "d-none"
                    );

                }


                const events =
                    payload.events
                    || [];


                timeline.replaceChildren();


                if (
                    events.length
                    === 0
                ) {

                    empty.classList.remove(
                        "d-none"
                    );

                }
                else {

                    empty.classList.add(
                        "d-none"
                    );


                    events.forEach(
                        function (
                            eventItem
                        ) {

                            timeline.appendChild(
                                createEventElement(
                                    eventItem
                                )
                            );

                        }
                    );

                }


                loading.classList.add(
                    "d-none"
                );

                content.classList.remove(
                    "d-none"
                );

            }
            catch (
                exception
            ) {

                loading.classList.add(
                    "d-none"
                );

                content.classList.add(
                    "d-none"
                );

                error.textContent =
                    (
                        exception.message
                        ||
                        "Não foi possível carregar o histórico."
                    );

                error.classList.remove(
                    "d-none"
                );

            }

        }


        modal.addEventListener(
            "show.bs.modal",
            function (
                event
            ) {

                resetModal();


                const button =
                    event.relatedTarget;


                if (!button) {

                    loading.classList.add(
                        "d-none"
                    );

                    error.textContent =
                        "Atividade não informada.";

                    error.classList.remove(
                        "d-none"
                    );

                    return;
                }


                const historyUrl =
                    button.dataset.historyUrl
                    || "";


                if (!historyUrl) {

                    loading.classList.add(
                        "d-none"
                    );

                    error.textContent =
                        "URL do histórico não informada.";

                    error.classList.remove(
                        "d-none"
                    );

                    return;
                }


                loadHistory(
                    historyUrl
                );

            }
        );


        modal.addEventListener(
            "hidden.bs.modal",
            function () {

                resetModal();

            }
        );

    }
);
