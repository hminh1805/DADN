from DADN.backend.data_manager import load_data

def generate_advices():
    data = load_data()
    sensors = data.get('sensors', {})
    temp = sensors.get('temp', 0)
    waterLevel = sensors.get('waterLevel', 100)
    motion = sensors.get('motion', 0)

    advices = []

    if waterLevel < 15:
        advices.append('⚠️ Cảnh báo: Lượng nước trong bình đang rất thấp, hãy châm thêm nước!')
    if temp > 32:
        advices.append('🔥 Nhiệt độ môi trường đang quá nóng, hệ thống quạt đang hoạt động hết công suất.')
    if temp < 18:
        advices.append('❄️ Trời đang lạnh, hãy đảm bảo bé cưng ở gần khu vực đèn sưởi.')
    if str(motion) in ['1', 'ON']:
        advices.append('🚨 Phát hiện thú cưng xâm nhập vào khu vực cấm!')

    if not advices:
        advices.append('✅ Mọi chỉ số đều ổn định. Thú cưng đang trong môi trường tốt.')

    return advices