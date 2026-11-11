/**
 * Manager dashboard leave-approval UI helpers.
 * Demo auth headers are attached for local demo only — not production-safe.
 */
(function (global) {
  "use strict";

  function showToast(message, isError) {
    var el = document.getElementById("toast");
    if (!el) return;
    el.textContent = message;
    el.hidden = false;
    el.classList.toggle("error-toast", !!isError);
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(function () {
      el.hidden = true;
    }, 3200);
  }

  function demoHeaders(cfg) {
    return {
      "Content-Type": "application/json",
      "X-User-Id": cfg.userId,
      "X-Role": cfg.role,
    };
  }

  function clientErrorMessage(payload) {
    var code = payload && payload.code;
    if (code === "not_pending") return "This request is no longer pending.";
    if (code === "insufficient_balance") return "Insufficient leave balance.";
    if (code === "forbidden") return "You are not allowed to approve this request.";
    if (code === "not_found") return "Leave request was not found.";
    if (code === "validation_error") return (payload && payload.message) || "Invalid request.";
    return (payload && payload.message) || "Approval failed.";
  }

  function initManagerDashboard(cfg) {
    var dialog = document.getElementById("approve-dialog");
    var form = document.getElementById("approve-form");
    var commentEl = document.getElementById("approve-comment");
    var errorEl = document.getElementById("dialog-error");
    var cancelBtn = document.getElementById("btn-cancel");
    var confirmBtn = document.getElementById("btn-confirm");
    var activeRequestId = null;
    var inFlight = false;

    function setError(msg) {
      if (!errorEl) return;
      if (!msg) {
        errorEl.hidden = true;
        errorEl.textContent = "";
        return;
      }
      errorEl.hidden = false;
      errorEl.textContent = msg;
    }

    function setInFlight(value) {
      inFlight = value;
      if (confirmBtn) confirmBtn.disabled = value;
      document.querySelectorAll("[data-action='open-approve']").forEach(function (btn) {
        btn.disabled = value;
      });
    }

    function openDialog(requestId) {
      activeRequestId = requestId;
      if (commentEl) commentEl.value = "";
      setError("");
      if (dialog && typeof dialog.showModal === "function") {
        dialog.showModal();
      }
    }

    function closeDialog() {
      activeRequestId = null;
      if (dialog && dialog.open) dialog.close();
    }

    document.querySelectorAll("[data-action='open-approve']").forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (inFlight) return;
        openDialog(btn.getAttribute("data-request-id"));
      });
    });

    if (cancelBtn) {
      cancelBtn.addEventListener("click", function () {
        // AC-10: dismiss = no API call
        closeDialog();
      });
    }

    if (dialog) {
      dialog.addEventListener("cancel", function () {
        // Esc dismiss — no API
        activeRequestId = null;
      });
    }

    if (form) {
      form.addEventListener("submit", function (ev) {
        ev.preventDefault();
        if (inFlight || !activeRequestId) return;

        var requestId = activeRequestId;
        var comment = commentEl ? commentEl.value : "";
        setInFlight(true);
        setError("");

        fetch("/api/leave-requests/" + encodeURIComponent(requestId) + "/approve", {
          method: "POST",
          headers: demoHeaders(cfg),
          body: JSON.stringify({ comment: comment }),
        })
          .then(function (res) {
            return res.json().then(function (body) {
              return { ok: res.ok, status: res.status, body: body };
            });
          })
          .then(function (result) {
            if (result.ok && result.status === 200) {
              // Success only: close dialog + toast + remove row
              closeDialog();
              showToast((result.body && result.body.message) || "Leave request approved.");
              var row = document.querySelector('tr[data-request-id="' + requestId + '"]');
              if (row && row.parentNode) row.parentNode.removeChild(row);
              var tbody = document.querySelector("#pending-table tbody");
              if (tbody && tbody.children.length === 0) {
                var table = document.getElementById("pending-table");
                if (table) {
                  var empty = document.createElement("p");
                  empty.className = "empty";
                  empty.textContent = "No pending leave requests.";
                  table.replaceWith(empty);
                }
              }
            } else {
              // 400/409: keep dialog open with error
              setError(clientErrorMessage(result.body));
            }
          })
          .catch(function () {
            setError("Network error. Please try again.");
          })
          .finally(function () {
            setInFlight(false);
          });
      });
    }
  }

  global.LeaveApproval = {
    initManagerDashboard: initManagerDashboard,
    showToast: showToast,
  };
})(window);
