/**
 * GOOGLE APPS SCRIPT — TỰ ĐỘNG LƯU DỮ LIỆU GARA THEO TỪNG THÁNG TRÊN GOOGLE DRIVE
 * CÁC CỘT: STT | Ngày | Biển Số | Hiệu Xe | Dịch vụ | Nội Dung | Báo Giá Dịch Vụ | Thanh Toán | Người Thực Hiện | Ghi Chú | Số Điện Thoại | Tên Khách Hàng (+ cột ID ẩn ở cuối)
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
  "Ghi Chú",
  "Số Điện Thoại",
  "Tên Khách Hàng",
];
const BASE_COLS = 10; // 10 cột chuẩn ban đầu

// Điền link Render của bạn vào đây (VD: "https://gara.onrender.com") để tự động giữ Server thức 24/24
const RENDER_APP_URL = "https://gara-dny6.onrender.com";

// Cache ID/URL thư mục 6 giờ để không phải tìm lại thư mục ở mỗi lần gọi
function getOrCreateFolder() {
  const cache = CacheService.getScriptCache();
  const cachedId = cache.get("folder_id");
  if (cachedId) {
    try {
      return DriveApp.getFolderById(cachedId);
    } catch (err) {
      // thư mục đã đổi -> tìm lại bên dưới
    }
  }
  const folders = DriveApp.getFoldersByName(FOLDER_NAME);
  const folder = folders.hasNext()
    ? folders.next()
    : DriveApp.createFolder(FOLDER_NAME);
  cache.put("folder_id", folder.getId(), 21600);
  cache.put("folder_url", folder.getUrl(), 21600);
  return folder;
}

function getFolderUrl() {
  const cached = CacheService.getScriptCache().get("folder_url");
  return cached || getOrCreateFolder().getUrl();
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

  // Cài đặt độ rộng tối ưu cho các cột
  sheet.setColumnWidth(1, 55); // STT
  sheet.setColumnWidth(2, 105); // Ngày
  sheet.setColumnWidth(3, 120); // Biển Số
  sheet.setColumnWidth(4, 135); // Hiệu Xe
  sheet.setColumnWidth(5, 160); // Dịch vụ
  sheet.setColumnWidth(6, 240); // Nội Dung
  sheet.setColumnWidth(7, 130); // Báo Giá Dịch Vụ
  sheet.setColumnWidth(8, 130); // Thanh Toán
  sheet.setColumnWidth(9, 130); // Người Thực Hiện
  sheet.setColumnWidth(10, 180); // Ghi Chú
  sheet.setColumnWidth(11, 120); // Số Điện Thoại
  sheet.setColumnWidth(12, 170); // Tên Khách Hàng
}

// Ghi 1 dòng ở dạng CHỮ (tránh Sheets tự đổi biển số như "50E-72167" thành số khoa học 0,00E+00)
function textFormats(n) {
  const f = ["General"];
  for (let i = 1; i < n; i++) f.push("@");
  return [f];
}

function appendRowAsText(sheet, values) {
  const row = sheet.getLastRow() + 1;
  const range = sheet.getRange(row, 1, 1, values.length);
  range.setNumberFormats(textFormats(values.length));
  range.setValues([values]);
  return row;
}

// Căn lề 1 dòng dữ liệu vừa thêm (gộp thành 2 lệnh thay vì 6)
function styleDataRow(sheet, row) {
  sheet
    .getRangeList(["A" + row, "B" + row, "C" + row, "E" + row, "H" + row])
    .setHorizontalAlignment("center");
  sheet.getRange(row, 7).setHorizontalAlignment("right");
}

const ID_COL = 13; // Cột ID ẩn (mã duy nhất của mỗi bản ghi) - nằm sau Số Điện Thoại và Tên Khách Hàng
const ID_HEADER = "ID";

function newId() {
  return Utilities.getUuid().replace(/-/g, "").slice(0, 12);
}

// Bảo đảm bố cục cột: [10 cột chuẩn] + Số Điện Thoại + Tên Khách Hàng + ID (ẩn).
// Tự nâng cấp sheet cũ mà không mất dữ liệu:
//   - Sheet 10 cột (chưa có gì ở cột K): thêm 2 cột mới + cột ID.
//   - Sheet bản trước (cột ID đang nằm ở K): chèn 2 cột mới phía trước để ID dịch sang M, dữ liệu giữ nguyên.
function ensureIdColumn(sheet) {
  if (sheet.getRange(1, ID_COL).getValue() !== ID_HEADER) {
    if (sheet.getRange(1, 11).getValue() === ID_HEADER) {
      sheet.insertColumnsBefore(11, 2);
      sheet.showColumns(11, 2);
    }
    sheet.getRange(1, ID_COL).setValue(ID_HEADER);
  }

  const extra = sheet.getRange(1, 11, 1, 2);
  const cur = extra.getValues()[0];
  if (cur[0] !== HEADERS[10] || cur[1] !== HEADERS[11]) {
    extra.setValues([[HEADERS[10], HEADERS[11]]]);
    extra.setBackground("#1E40AF");
    extra.setFontColor("#FFFFFF");
    extra.setFontWeight("bold");
    extra.setHorizontalAlignment("center");
    extra.setVerticalAlignment("middle");
    sheet.setColumnWidth(11, 120);
    sheet.setColumnWidth(12, 170);
  }

  if (!sheet.isColumnHiddenByUser(ID_COL)) {
    sheet.hideColumns(ID_COL);
  }
}

// Gán ID cho các dòng cũ chưa có ID
function ensureIds(sheet) {
  const last = sheet.getLastRow();
  if (last < 2) return;
  const range = sheet.getRange(2, ID_COL, last - 1, 1);
  const vals = range.getValues();
  let changed = false;
  for (let i = 0; i < vals.length; i++) {
    if (!vals[i][0]) {
      vals[i][0] = newId();
      changed = true;
    }
  }
  if (changed) {
    range.setNumberFormat("@");
    range.setValues(vals);
  }
}

function findRowById(sheet, id) {
  const last = sheet.getLastRow();
  if (last < 2 || !id) return -1;
  const ids = sheet.getRange(2, ID_COL, last - 1, 1).getValues();
  for (let i = 0; i < ids.length; i++) {
    if (String(ids[i][0]) === String(id)) return i + 2;
  }
  return -1;
}

function renumberStt(sheet) {
  const last = sheet.getLastRow();
  if (last < 2) return;
  const nums = [];
  for (let r = 2; r <= last; r++) nums.push([r - 1]);
  const range = sheet.getRange(2, 1, last - 1, 1);
  range.setNumberFormat("General");
  range.setValues(nums);
}

// Chỉ cho 1 yêu cầu ghi chạy tại một thời điểm (tránh trùng STT / ghi chồng)
function withLock(fn) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    return fn();
  } finally {
    lock.releaseLock();
  }
}

function getOrCreateMonthlySheet(monthKey) {
  const mk = monthKey || Utilities.formatDate(new Date(), "GMT+7", "MM_yyyy");

  // Đường nhanh: đã từng kiểm tra bảng tháng này -> mở thẳng bằng ID, bỏ qua duyệt thư mục
  const cachedId = CacheService.getScriptCache().get("ss2_" + mk);
  if (cachedId) {
    try {
      return SpreadsheetApp.openById(cachedId);
    } catch (err) {
      // cache hỏng -> tìm lại bên dưới
    }
  }

  const fileName = "gara_" + mk;
  const folder = getOrCreateFolder();
  const files = folder.getFilesByName(fileName);

  let ss;
  if (files.hasNext()) {
    const file = files.next();
    ss = SpreadsheetApp.open(file);
    const sheet = ss.getActiveSheet();
    // Tự động dựng lại tiêu đề nếu file hỏng / quá cũ (chưa đủ 10 cột chuẩn)
    if (
      sheet.getLastColumn() < BASE_COLS ||
      sheet.getRange(1, 1).getValue() !== "STT"
    ) {
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

  ensureIdColumn(ss.getActiveSheet());
  CacheService.getScriptCache().put("ss2_" + mk, ss.getId(), 3600);
  return ss;
}

// Đường đọc nhanh: bảng tháng đã có sẵn và đủ ID -> đọc ngay, không cần khóa / duyệt thư mục
function tryFastList(monthKey) {
  const id = CacheService.getScriptCache().get("ss2_" + monthKey);
  if (!id) return null;
  let ss;
  try {
    ss = SpreadsheetApp.openById(id);
  } catch (err) {
    return null;
  }
  const sheet = ss.getActiveSheet();
  if (sheet.getRange(1, ID_COL).getValue() !== ID_HEADER) return null;
  const records = readRecordsFromSheet(ss, monthKey);
  if (
    records.some(function (r) {
      return !r.id;
    })
  )
    return null;
  return jsonResponse({
    success: true,
    month_key: monthKey,
    file_url: ss.getUrl(),
    folder_url: getFolderUrl(),
    records: records,
  });
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
        file_url: f.getUrl(),
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
    const numCols = Math.max(sheet.getLastColumn(), ID_COL);
    const values = sheet
      .getRange(2, 1, lastRow - 1, numCols)
      .getDisplayValues();
    for (let i = 0; i < values.length; i++) {
      const row = values[i];
      if (!row[1] && !row[2] && !row[3] && !row[5]) continue;
      records.push({
        id: row[ID_COL - 1] || "",
        row_id: i + 2,
        stt: row[0] || i + 1,
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
        so_dien_thoai: row[10] || "",
        ten_khach_hang: row[11] || "",
      });
    }
  }
  return records;
}

function doGet(e) {
  try {
    const params = (e && e.parameter) || {};
    const action = params.action || "list";
    const monthKey =
      params.month_key || Utilities.formatDate(new Date(), "GMT+7", "MM_yyyy");

    if (action === "months") {
      return jsonResponse({
        success: true,
        months: listAvailableMonths(),
        folder_url: getFolderUrl(),
      });
    }

    if (action === "list") {
      const fast = tryFastList(monthKey);
      if (fast) return fast;
    }

    return withLock(function () {
      const ss = getOrCreateMonthlySheet(monthKey);
      const sheet = ss.getActiveSheet();
      const fileUrl = ss.getUrl();

      // THÊM bản ghi (an toàn khi gửi lại: cùng ID thì không ghi trùng)
      if (action === "append") {
        if (!params.bien_so)
          return jsonResponse({ success: false, error: "Thiếu biển số" });

        const id = params.id || newId();
        const existing = findRowById(sheet, id);
        if (existing > 0) {
          return jsonResponse({
            success: true,
            duplicate: true,
            id: id,
            row_id: existing,
            stt: sheet.getRange(existing, 1).getValue(),
            file_url: fileUrl,
            folder_url: getFolderUrl(),
          });
        }

        const stt = Math.max(sheet.getLastRow(), 1);
        const ngay =
          params.ngay ||
          Utilities.formatDate(new Date(), "GMT+7", "dd/MM/yyyy");
        const newRow = appendRowAsText(sheet, [
          stt,
          ngay,
          (params.bien_so || "").toUpperCase(),
          params.hieu_xe || "",
          params.dich_vu || "Bảo Trì & Sửa Chữa",
          params.noi_dung || "",
          params.bao_gia || "",
          params.thanh_toan || "Chưa Thanh Toán",
          params.nguoi_thuc_hien || "",
          params.ghi_chu || "",
          params.so_dien_thoai || "",
          params.ten_khach_hang || "",
          id,
        ]);
        styleDataRow(sheet, newRow);

        return jsonResponse({
          success: true,
          id: id,
          row_id: newRow,
          stt: stt,
          file_url: fileUrl,
          folder_url: getFolderUrl(),
        });
      }

      // SỬA / XÓA: tìm dòng theo ID (không phụ thuộc số dòng)
      if (action === "update" || action === "delete") {
        const row = findRowById(sheet, params.id);
        if (row < 2) {
          return jsonResponse({
            success: false,
            not_found: true,
            error: "Không tìm thấy bản ghi (có thể đã bị xóa).",
          });
        }

        if (action === "update") {
          const range = sheet.getRange(row, 2, 1, 11);
          range.setNumberFormats([
            ["@", "@", "@", "@", "@", "@", "@", "@", "@", "@", "@"],
          ]);
          range.setValues([
            [
              params.ngay || "",
              (params.bien_so || "").toUpperCase(),
              params.hieu_xe || "",
              params.dich_vu || "Bảo Trì & Sửa Chữa",
              params.noi_dung || "",
              params.bao_gia || "",
              params.thanh_toan || "Chưa Thanh Toán",
              params.nguoi_thuc_hien || "",
              params.ghi_chu || "",
              params.so_dien_thoai || "",
              params.ten_khach_hang || "",
            ],
          ]);
          return jsonResponse({
            success: true,
            id: params.id,
            file_url: fileUrl,
          });
        }

        sheet.deleteRow(row);
        renumberStt(sheet);
        return jsonResponse({ success: true, file_url: fileUrl });
      }

      // DANH SÁCH
      ensureIds(sheet);
      return jsonResponse({
        success: true,
        month_key: monthKey,
        file_url: fileUrl,
        folder_url: getFolderUrl(),
        records: readRecordsFromSheet(ss, monthKey),
      });
    });
  } catch (err) {
    return jsonResponse({ success: false, error: err.toString() });
  }
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON,
  );
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
      muteHttpExceptions: true,
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
  ScriptApp.newTrigger("keepRenderAwake").timeBased().everyMinutes(10).create();
  Logger.log("Đã bật chế độ giữ Server Render thức 24/24 (Ping mỗi 10 phút)!");
}
