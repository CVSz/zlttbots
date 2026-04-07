import type { CopyRequest, OptimizeRequest, TrendProduct } from "./schemas.js";

export function calculateMomentum(product: TrendProduct): number {
  const ctr = product.impressions === 0 ? 0 : product.clicks / product.impressions;
  const cvr = product.clicks === 0 ? 0 : product.conversions / product.clicks;
  return Number((ctr * 0.55 + cvr * 0.45).toFixed(4));
}

export function rankProducts(products: TrendProduct[]) {
  return products
    .map((product) => ({
      ...product,
      momentumScore: calculateMomentum(product),
    }))
    .sort((a, b) => b.momentumScore - a.momentumScore)
    .slice(0, 10);
}

export function generateCaption(input: CopyRequest): string {
  const highlights = input.valueProps.slice(0, 3).join(" • ");
  if (input.tone === "expert") {
    return `วิเคราะห์แล้วว่า ${input.productName} เหมาะกับ ${input.audience} เพราะ ${highlights}. ถ้าต้องการผลลัพธ์ที่วัดได้ เริ่มทดลองวันนี้และติดตาม KPI แบบรายสัปดาห์.`;
  }

  if (input.tone === "urgent") {
    return `${input.audience} ห้ามพลาด! ${input.productName} จุดเด่นคือ ${highlights}. โปรรอบนี้มีจำกัด รีบเช็กก่อนหมด.`;
  }

  return `${input.productName} สำหรับ ${input.audience} ที่อยากได้ ${highlights}. ใช้ง่าย เห็นผลเร็ว และคุ้มค่าสุด ๆ`;
}

const feedbackMap: Record<OptimizeRequest["feedback"][number], string> = {
  too_long: "สรุปให้อ่านง่ายใน 1 ประโยค",
  not_clear: "ชี้ประโยชน์หลักให้ชัด",
  low_emotion: "เพิ่มอารมณ์ร่วมและความเร่งด่วน",
  weak_cta: "ปิดท้ายด้วยคำชวนลงมือทำ",
};

export function optimizeCaption(input: OptimizeRequest): string {
  const directives = input.feedback.map((item) => feedbackMap[item]).join(" + ");
  return `สำหรับ ${input.audience}: ${input.currentCaption} | ปรับตามข้อเสนอ: ${directives}. CTA: กดดูรายละเอียดและเริ่มได้ทันที`;
}
