/**
 * GOOGLE APPS SCRIPT — TỰ ĐỘNG LƯU DỮ LIỆU GARA THEO TỪNG THÁNG TRÊN GOOGLE DRIVE
 *
 * HƯỚNG DẪN CÀI ĐẶT (CHỈ MẤT 1 PHÚT):
 * 1. Truy cập https://script.google.com -> Bấm "Dự án mới" (New project).
 * 2. Xóa toàn bộ mã cũ và dán toàn bộ nội dung file này vào.
 * 3. Bấm nút "Triển khai" (Deploy) ở góc phải trên -> Chọn "Tùy chọn triển khai mới" (New deployment).
 * 4. Ở mục "Chọn loại" (bánh răng) -> Chọn "Ứng dụng web" (Web app):
 *    - Thực thi dưới dạng (Execute as): "Tôi" (Me)
 *    - Ai có quyền truy cập (Who has access): Chọn "Bất kỳ ai" (Anyone)
 * 5. Bấm "Triển khai" (Deploy) -> Cấp quyền truy cập Google Drive -> Copy đường link "URL ứng dụng web" (kết thúc bằng /exec).
 * 6. Dán đường link đó vào phần Cài đặt Google Drive trên giao diện Web Gara Voice (hoặc biến môi trường DRIVE_WEBHOOK_URL).
 */

const FOLDER_NAME = "Gara_Data";
const HEADERS = ["Thời gian", "Biển số", "Hãng xe", "Dịch vụ", "Giá", "Người phụ trách"];

function getOrCreateFolder() {
  const folders = DriveApp.getFoldersByName(FOLDER_NAME);
  if (folders.hasNext()) {
    return folders.next();
  }
  return DriveApp.createFolder(FOLDER_NAME);
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
    // Tự động bổ sung cột thứ 6 "Người phụ trách" nếu file cũ mới chỉ có 5 cột
    if (sheet.getLastColumn() < HEADERS.length || sheet.getRange(1, 6).getValue() !== "Người phụ trách") {
      sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
      const headerRange = sheet.getRange(1, 1, 1, HEADERS.length);
      headerRange.setBackground("#1E40AF");
      headerRange.setFontColor("#FFFFFF");
      headerRange.setFontWeight("bold");
      headerRange.setHorizontalAlignment("center");
      sheet.setColumnWidth(6, 150);
    }
  } else {
    ss = SpreadsheetApp.create(fileName);
    const file = DriveApp.getFileById(ss.getId());
    folder.addFile(file);
    DriveApp.getRootFolder().removeFile(file);

    const sheet = ss.getActiveSheet();
    sheet.setName("Thang_" + mk);
    sheet.appendRow(HEADERS);

    // Định dạng dòng tiêu đề đẹp mắt
    const headerRange = sheet.getRange(1, 1, 1, HEADERS.length);
    headerRange.setBackground("#1E40AF");
    headerRange.setFontColor("#FFFFFF");
    headerRange.setFontWeight("bold");
    headerRange.setHorizontalAlignment("center");
    sheet.setFrozenRows(1);
    sheet.setColumnWidth(1, 120);
    sheet.setColumnWidth(2, 130);
    sheet.setColumnWidth(3, 130);
    sheet.setColumnWidth(4, 210);
    sheet.setColumnWidth(5, 120);
    sheet.setColumnWidth(6, 150);
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
    const values = sheet.getRange(2, 1, lastRow - 1, 6).getDisplayValues();
    for (let i = 0; i < values.length; i++) {
      const row = values[i];
      if (!row[0] && !row[1] && !row[2] && !row[3] && !row[4] && !row[5]) continue;
      records.push({
        row_id: i + 2,
        month_key: monthKey,
        thoi_gian: row[0],
        bien_so: row[1],
        hang_xe: row[2],
        dich_vu: row[3],
        gia: row[4],
        nguoi_phu_trach: row[5] || ""
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

    // Hỗ trợ thêm dòng hoặc xóa dòng ngay cả khi HTTP Redirect 302 chuyển POST thành GET
    if (action === "append" && params.bien_so) {
      sheet.appendRow([
        params.thoi_gian || "",
        params.bien_so || "",
        params.hang_xe || "",
        params.dich_vu || "",
        params.gia || "",
        params.nguoi_phu_trach || ""
      ]);
      return jsonResponse({
        success: true,
        row_id: sheet.getLastRow(),
        file_url: ss.getUrl(),
        folder_url: getOrCreateFolder().getUrl()
      });
    }

    if (action === "delete" && params.row_id) {
      const rowId = parseInt(params.row_id, 10);
      if (rowId >= 2 && rowId <= sheet.getLastRow()) {
        sheet.deleteRow(rowId);
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
      const rec = body.record || {};
      sheet.appendRow([
        rec.thoi_gian || "",
        rec.bien_so || "",
        rec.hang_xe || "",
        rec.dich_vu || "",
        rec.gia || "",
        rec.nguoi_phu_trach || ""
      ]);
      const newRow = sheet.getLastRow();
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
