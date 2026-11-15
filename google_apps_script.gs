/**
 * GOOGLE APPS SCRIPT — TỰ ĐỘNG LƯU DỮ LIỆU GARA THEO TỪNG THÁNG TRÊN GOOGLE DRIVE
 * 10 CỘT CHUẨN: STT | Ngày | Biển Số | Hiệu Xe | Dịch vụ | Nội Dung | Báo Giá Dịch Vụ | Thanh Toán | Người Thực Hiện | Ghi Chú
 *
 * HƯỚNG DẪN CÀI ĐẶT / CẬP NHẬT:
 * 1. Truy cập https://script.google.com -> Mở dự án Gara của bạn.
 * 2. Xóa toàn bộ mã cũ và dán toàn bộ nội dung file này vào.
 * 3. Bấm nút "Triển khai" (Deploy) ở góc phải trên -> "Quản lý bản triển khai" (Manage deployments).
 * 4. Bấm biểu tượng cây bút (Chỉnh sửa) -> Chọn "Phiên bản mới" (New version) -> Bấm "Triển khai" (Deploy).
 * 5. Giữ nguyên URL Webhook (hoặc copy lại nếu tạo bản mới) để hệ thống tự động ghi 10 cột lên Google Sheets.
 */

const FOLDER_NAME = "Gara_Data";
const HEADERS = [
  "STT",
  "Ngày",
  "Biển Số",
  "Hiệu Xe",
  "Dịch vụ",
  "Nội Dung",
  "Báo Giá Dịch Vụ",
  "Thanh Toán",
  "Người Thực Hiện",
  "Ghi Chú"
];

// Điền link Render của bạn vào đây (VD: "https://gara.onrender.com") để tự động giữ Server thức 24/24
const RENDER_APP_URL = "https://gara.onrender.com";

function getOrCreateFolder() {
  const folders = DriveApp.getFoldersByName(FOLDER_NAME);
  if (folders.hasNext()) {
    return folders.next();
  }
  return DriveApp.createFolder(FOLDER_NAME);
}

function applyHeaderStyling(sheet) {
  const headerRange = sheet.getRange(1, 1, 1, HEADERS.length);
  headerRange.setValues([HEADERS]);
  headerRange.setBackground("#1E40AF");
  headerRange.setFontColor("#FFFFFF");
  headerRange.setFontWeight("bold");
  headerRange.setHorizontalAlignment("center");
  headerRange.setVerticalAlignment("middle");
  sheet.setFrozenRows(1);
  sheet.setRowHeight(1, 32);

  // Cài đặt độ rộng tối ưu cho 10 cột
  sheet.setColumnWidth(1, 55);   // STT
  sheet.setColumnWidth(2, 105);  // Ngày
  sheet.setColumnWidth(3, 120);  // Biển Số
  sheet.setColumnWidth(4, 135);  // Hiệu Xe
  sheet.setColumnWidth(5, 160);  // Dịch vụ
  sheet.setColumnWidth(6, 240);  // Nội Dung
  sheet.setColumnWidth(7, 130);  // Báo Giá Dịch Vụ
  sheet.setColumnWidth(8, 130);  // Thanh Toán
  sheet.setColumnWidth(9, 130);  // Người Thực Hiện
  sheet.setColumnWidth(10, 180); // Ghi Chú
}

function getOrCreateMonthlySheet(monthKey) {
  const mk = monthKey || "11_2026";
  const fileName = "gara_" + mk;
  const folder = getOrCreateFolder();
  const files = folder.getFilesByName(fileName);

  let ss;
  if (files.hasNext()) {
    const file = files.next();
    ss = SpreadsheetApp.open(file);
    const sheet = ss.getActiveSheet();
    // Tự động nâng cấp lên 10 cột chuẩn nếu file cũ chưa đủ
    if (sheet.getLastColumn() < HEADERS.length || sheet.getRange(1, 1).getValue() !== "STT") {
      applyHeaderStyling(sheet);
    }
  } else {
    ss = SpreadsheetApp.create(fileName);
    const file = DriveApp.getFileById(ss.getId());
    folder.addFile(file);
    DriveApp.getRootFolder().removeFile(file);

    const sheet = ss.getActiveSheet();
    sheet.setName("Thang_" + mk);
    applyHeaderStyling(sheet);
  }

  return ss;
}

function listAvailableMonths() {
  const folder = getOrCreateFolder();
  const files = folder.getFiles();
  const months = [];

  while (files.hasNext()) {
    const f = files.next();
    const name = f.getName();
    const m = name.match(/^gara_(\d{2})_(\d{4})$/);
    if (m) {
      months.push({
        month_key: m[1] + "_" + m[2],
        label: "Tháng " + m[1] + "/" + m[2],
        filename: name + ".xlsx",
        file_url: f.getUrl()
      });
    }
  }
  return months;
}

function readRecordsFromSheet(ss, monthKey) {
  const sheet = ss.getActiveSheet();
  const lastRow = sheet.getLastRow();
  const records = [];

  if (lastRow >= 2) {
    const numCols = Math.max(sheet.getLastColumn(), HEADERS.length);
    const values = sheet.getRange(2, 1, lastRow - 1, numCols).getDisplayValues();
    for (let i = 0; i < values.length; i++) {
      const row = values[i];
      if (!row[1] && !row[2] && !row[3] && !row[5]) continue;
      records.push({
        row_id: i + 2,
        stt: row[0] || (i + 1),
        month_key: monthKey,
        ngay: row[1] || "",
        bien_so: row[2] || "",
        hieu_xe: row[3] || "",
        dich_vu: row[4] || "Bảo Trì & Sửa Chữa",
        noi_dung: row[5] || "",
        bao_gia: row[6] || "",
        thanh_toan: row[7] || "Chưa Thanh Toán",
        nguoi_thuc_hien: row[8] || "",
        ghi_chu: row[9] || "",
        // Tương thích ngược:
        thoi_gian: row[1] || "",
        hang_xe: row[3] || "",
        gia: row[6] || "",
        nguoi_phu_trach: row[8] || ""
      });
    }
  }
  return records;
}

function doGet(e) {
  try {
    const params = (e && e.parameter) || {};
    const action = params.action || "list";
    const monthKey = params.month_key || "11_2026";

    if (action === "months") {
      return jsonResponse({
        success: true,
        months: listAvailableMonths(),
        folder_url: getOrCreateFolder().getUrl()
      });
    }

    const ss = getOrCreateMonthlySheet(monthKey);
    const sheet = ss.getActiveSheet();

    // Hỗ trợ thêm bản ghi ngay cả khi HTTP Redirect 302 chuyển POST thành GET
    if (action === "append" && params.bien_so) {
      const lastRow = sheet.getLastRow();
      const stt = params.stt || (lastRow >= 1 ? lastRow : 1);
      const ngay = params.ngay || params.thoi_gian || Utilities.formatDate(new Date(), "GMT+7", "dd/MM/yyyy");
      const bienSo = (params.bien_so || "").toUpperCase();
      const hieuXe = params.hieu_xe || params.hang_xe || "";
      const dichVu = params.dich_vu || "Bảo Trì & Sửa Chữa";
      const noiDung = params.noi_dung || "";
      const baoGia = params.bao_gia || params.gia || "";
      const thanhToan = params.thanh_toan || "Chưa Thanh Toán";
      const nguoiThucHien = params.nguoi_thuc_hien || params.nguoi_phu_trach || "";
      const ghiChu = params.ghi_chu || "";

      sheet.appendRow([
        stt,
        ngay,
        bienSo,
        hieuXe,
        dichVu,
        noiDung,
        baoGia,
        thanhToan,
        nguoiThucHien,
        ghiChu
      ]);

      const newRow = sheet.getLastRow();
      sheet.getRange(newRow, 1).setHorizontalAlignment("center");
      sheet.getRange(newRow, 2).setHorizontalAlignment("center");
      sheet.getRange(newRow, 3).setHorizontalAlignment("center");
      sheet.getRange(newRow, 5).setHorizontalAlignment("center");
      sheet.getRange(newRow, 7).setHorizontalAlignment("right");
      sheet.getRange(newRow, 8).setHorizontalAlignment("center");

      return jsonResponse({
        success: true,
        row_id: newRow,
        file_url: ss.getUrl(),
        folder_url: getOrCreateFolder().getUrl()
      });
    }

    if (action === "delete" && params.row_id) {
      const rowId = parseInt(params.row_id, 10);
      if (rowId >= 2 && rowId <= sheet.getLastRow()) {
        sheet.deleteRow(rowId);
        // Tái lập lại STT 1..N
        for (let r = 2; r <= sheet.getLastRow(); r++) {
          sheet.getRange(r, 1).setValue(r - 1);
        }
        return jsonResponse({ success: true, file_url: ss.getUrl() });
      }
      return jsonResponse({ success: false, error: "Row out of bounds" });
    }

    const records = readRecordsFromSheet(ss, monthKey);
    return jsonResponse({
      success: true,
      month_key: monthKey,
      file_url: ss.getUrl(),
      folder_url: getOrCreateFolder().getUrl(),
      months: listAvailableMonths(),
      records: records
    });
  } catch (err) {
    return jsonResponse({ success: false, error: err.toString() });
  }
}

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents || "{}");
    const action = body.action || "append";
    const monthKey = body.month_key || "11_2026";
    const ss = getOrCreateMonthlySheet(monthKey);
    const sheet = ss.getActiveSheet();

    if (action === "append") {
      const rec = body.record || body;
      const lastRow = sheet.getLastRow();
      const stt = rec.stt || (lastRow >= 1 ? lastRow : 1);
      const ngay = rec.ngay || rec.thoi_gian || Utilities.formatDate(new Date(), "GMT+7", "dd/MM/yyyy");
      const bienSo = (rec.bien_so || "").toUpperCase();
      const hieuXe = rec.hieu_xe || rec.hang_xe || "";
      const dichVu = rec.dich_vu || "Bảo Trì & Sửa Chữa";
      const noiDung = rec.noi_dung || "";
      const baoGia = rec.bao_gia || rec.gia || "";
      const thanhToan = rec.thanh_toan || "Chưa Thanh Toán";
      const nguoiThucHien = rec.nguoi_thuc_hien || rec.nguoi_phu_trach || "";
      const ghiChu = rec.ghi_chu || "";

      sheet.appendRow([
        stt,
        ngay,
        bienSo,
        hieuXe,
        dichVu,
        noiDung,
        baoGia,
        thanhToan,
        nguoiThucHien,
        ghiChu
      ]);

      const newRow = sheet.getLastRow();
      sheet.getRange(newRow, 1).setHorizontalAlignment("center");
      sheet.getRange(newRow, 2).setHorizontalAlignment("center");
      sheet.getRange(newRow, 3).setHorizontalAlignment("center");
      sheet.getRange(newRow, 5).setHorizontalAlignment("center");
      sheet.getRange(newRow, 7).setHorizontalAlignment("right");
      sheet.getRange(newRow, 8).setHorizontalAlignment("center");

      return jsonResponse({
        success: true,
        row_id: newRow,
        file_url: ss.getUrl(),
        folder_url: getOrCreateFolder().getUrl()
      });
    }

    if (action === "delete") {
      const rowId = parseInt(body.row_id, 10);
      if (rowId >= 2 && rowId <= sheet.getLastRow()) {
        sheet.deleteRow(rowId);
        for (let r = 2; r <= sheet.getLastRow(); r++) {
          sheet.getRange(r, 1).setValue(r - 1);
        }
        return jsonResponse({ success: true, file_url: ss.getUrl() });
      }
      return jsonResponse({ success: false, error: "Row out of bounds" });
    }

    return jsonResponse({
      success: true,
      file_url: ss.getUrl(),
      records: readRecordsFromSheet(ss, monthKey)
    });
  } catch (err) {
    return jsonResponse({ success: false, error: err.toString() });
  }
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * CHỐNG NGỦ ĐÔNG TRÊN RENDER FREE (KEEP-ALIVE 24/24):
 * Tự động ping vào /health mỗi 10 phút để Web Gara luôn thức 24/24.
 */
function keepRenderAwake() {
  const baseUrl = (RENDER_APP_URL || "").trim().replace(/\/+$/, "");
  if (!baseUrl) return;
  try {
    const res = UrlFetchApp.fetch(baseUrl + "/health", {
      method: "get",
      muteHttpExceptions: true
    });
    Logger.log("Ping /health status: " + res.getResponseCode());
  } catch (err) {
    Logger.log("Ping error: " + err.toString());
  }
}

function setupKeepAliveTrigger() {
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === "keepRenderAwake") {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }
  ScriptApp.newTrigger("keepRenderAwake")
    .timeBased()
    .everyMinutes(10)
    .create();
  Logger.log("Đã bật chế độ giữ Server Render thức 24/24 (Ping mỗi 10 phút)!");
}
