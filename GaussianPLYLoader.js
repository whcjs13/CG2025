// GaussianPLYLoader.js
import * as THREE from "three";

export class GaussianPLYLoader {
  constructor() {}

  /**
   * 3DGS 스타일 binary_little_endian PLY를 파싱해서
   * THREE.BufferGeometry로 반환
   * @param {ArrayBuffer} arrayBuffer
   * @returns {THREE.BufferGeometry}
   */
  parse(arrayBuffer) {
    const textDecoder = new TextDecoder("utf-8");
    const headerText = textDecoder.decode(arrayBuffer);

    // 1. header 구간 찾기
    const endHeaderIndex = headerText.indexOf("end_header");
    if (endHeaderIndex === -1) {
      throw new Error("PLY header does not contain 'end_header'");
    }

    // 'end_header' 뒤의 첫 번째 줄바꿈까지 포함
    const nlIndex = headerText.indexOf("\n", endHeaderIndex);
    const headerEndCharIndex = nlIndex >= 0 ? nlIndex + 1 : endHeaderIndex + "end_header".length;
    const header = headerText.substring(0, headerEndCharIndex);

    // ASCII라서 char index == byte offset 이라고 가정 (PLY header는 ASCII)
    const headerEndByteOffset = headerEndCharIndex;

    // 2. header 파싱: vertex 개수, property 목록
    const lines = header.split(/\r?\n/);
    let vertexCount = 0;
    let isBinaryLittleEndian = false;

    const properties = []; // { name: string, type: string }

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      if (trimmed.startsWith("format")) {
        // 예: "format binary_little_endian 1.0"
        if (trimmed.includes("binary_little_endian")) {
          isBinaryLittleEndian = true;
        }
      } else if (trimmed.startsWith("element vertex")) {
        // 예: "element vertex 12345"
        const parts = trimmed.split(/\s+/);
        vertexCount = parseInt(parts[2], 10);
      } else if (trimmed.startsWith("property")) {
        // 예: "property float x"
        const parts = trimmed.split(/\s+/);
        if (parts.length >= 3) {
          const type = parts[1];   // float, float32, double 등
          const name = parts[2];
          properties.push({ name, type });
        }
      }
    }

    if (!isBinaryLittleEndian) {
      console.warn("GaussianPLYLoader: expected binary_little_endian format.");
    }
    if (!vertexCount) {
      throw new Error("GaussianPLYLoader: no 'element vertex' found in header.");
    }

    // 3. 타입별 바이트 크기
    function typeByteSize(type) {
      switch (type) {
        case "float":
        case "float32":
          return 4;
        case "double":
        case "float64":
          return 8;
        case "uchar":
        case "uint8":
        case "char":
        case "int8":
          return 1;
        case "ushort":
        case "uint16":
        case "short":
        case "int16":
          return 2;
        case "uint":
        case "uint32":
        case "int":
        case "int32":
          return 4;
        default:
          // 3DGS PLY에서는 거의 안 쓰이므로, 일단 4로 가정
          console.warn("GaussianPLYLoader: unknown property type:", type, "-> assuming 4 bytes");
          return 4;
      }
    }

    const littleEndian = true;
    const dv = new DataView(arrayBuffer, headerEndByteOffset);

    // vertex당 stride 계산
    let stride = 0;
    for (const p of properties) {
      stride += typeByteSize(p.type);
    }

    // 4. 우리가 관심 있는 속성들에 대한 배열 준비
    const positions = new Float32Array(vertexCount * 3);

    const hasScale0 = properties.some((p) => p.name === "scale_0");
    const hasScale1 = properties.some((p) => p.name === "scale_1");
    const hasScale2 = properties.some((p) => p.name === "scale_2");
    const hasRot0 = properties.some((p) => p.name === "rot_0");
    const hasRot1 = properties.some((p) => p.name === "rot_1");
    const hasRot2 = properties.some((p) => p.name === "rot_2");
    const hasRot3 = properties.some((p) => p.name === "rot_3");
    const hasFdc0 = properties.some((p) => p.name === "f_dc_0");
    const hasFdc1 = properties.some((p) => p.name === "f_dc_1");
    const hasFdc2 = properties.some((p) => p.name === "f_dc_2");
    const hasOpacity = properties.some((p) => p.name === "opacity");

    const scale0 = hasScale0 ? new Float32Array(vertexCount) : null;
    const scale1 = hasScale1 ? new Float32Array(vertexCount) : null;
    const scale2 = hasScale2 ? new Float32Array(vertexCount) : null;
    const rot0 = hasRot0 ? new Float32Array(vertexCount) : null;
    const rot1 = hasRot1 ? new Float32Array(vertexCount) : null;
    const rot2 = hasRot2 ? new Float32Array(vertexCount) : null;
    const rot3 = hasRot3 ? new Float32Array(vertexCount) : null;
    const fdc0 = hasFdc0 ? new Float32Array(vertexCount) : null;
    const fdc1 = hasFdc1 ? new Float32Array(vertexCount) : null;
    const fdc2 = hasFdc2 ? new Float32Array(vertexCount) : null;
    const opacity = hasOpacity ? new Float32Array(vertexCount) : null;

    // 5. vertex 버퍼 파싱
    let offset = 0; // DataView 내 오프셋

    for (let i = 0; i < vertexCount; i++) {
      let vertexOffset = offset;

      let x = 0, y = 0, z = 0;

      for (const p of properties) {
        const name = p.name;
        const byteSize = typeByteSize(p.type);

        let value = 0;

        // 3DGS에서는 float32가 대부분이지만, 몇 가지 타입은 안전하게 처리
        switch (p.type) {
          case "float":
          case "float32":
            value = dv.getFloat32(vertexOffset, littleEndian);
            break;
          case "double":
          case "float64":
            value = dv.getFloat64(vertexOffset, littleEndian);
            break;
          case "uchar":
          case "uint8":
            value = dv.getUint8(vertexOffset);
            break;
          case "char":
          case "int8":
            value = dv.getInt8(vertexOffset);
            break;
          case "ushort":
          case "uint16":
            value = dv.getUint16(vertexOffset, littleEndian);
            break;
          case "short":
          case "int16":
            value = dv.getInt16(vertexOffset, littleEndian);
            break;
          case "uint":
          case "uint32":
            value = dv.getUint32(vertexOffset, littleEndian);
            break;
          case "int":
          case "int32":
            value = dv.getInt32(vertexOffset, littleEndian);
            break;
          default:
            // 모르는 타입은 그냥 0으로 두고 건너뜀
            break;
        }

        // 이름에 따라 우리가 만든 배열에 채우기
        if (name === "x") {
          x = value;
        } else if (name === "y") {
          y = value;
        } else if (name === "z") {
          z = value;
        } else if (name === "scale_0" && scale0) {
          scale0[i] = value;
        } else if (name === "scale_1" && scale1) {
          scale1[i] = value;
        } else if (name === "scale_2" && scale2) {
          scale2[i] = value;
        } else if (name === "rot_0" && rot0) {
          rot0[i] = value;
        } else if (name === "rot_1" && rot1) {
          rot1[i] = value;
        } else if (name === "rot_2" && rot2) {
          rot2[i] = value;
        } else if (name === "rot_3" && rot3) {
          rot3[i] = value;
        } else if (name === "f_dc_0" && fdc0) {
          fdc0[i] = value;
        } else if (name === "f_dc_1" && fdc1) {
          fdc1[i] = value;
        } else if (name === "f_dc_2" && fdc2) {
          fdc2[i] = value;
        } else if (name === "opacity" && opacity) {
          opacity[i] = value;
        }

        vertexOffset += byteSize;
      }

      // position 저장
      positions[3 * i + 0] = x;
      positions[3 * i + 1] = y;
      positions[3 * i + 2] = z;

      offset += stride;
    }

    // 6. BufferGeometry 구성
    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));

    if (scale0) geom.setAttribute("scale_0", new THREE.BufferAttribute(scale0, 1));
    if (scale1) geom.setAttribute("scale_1", new THREE.BufferAttribute(scale1, 1));
    if (scale2) geom.setAttribute("scale_2", new THREE.BufferAttribute(scale2, 1));
    if (rot0)   geom.setAttribute("rot_0",   new THREE.BufferAttribute(rot0, 1));
    if (rot1)   geom.setAttribute("rot_1",   new THREE.BufferAttribute(rot1, 1));
    if (rot2)   geom.setAttribute("rot_2",   new THREE.BufferAttribute(rot2, 1));
    if (rot3)   geom.setAttribute("rot_3",   new THREE.BufferAttribute(rot3, 1));
    if (fdc0)   geom.setAttribute("f_dc_0",  new THREE.BufferAttribute(fdc0, 1));
    if (fdc1)   geom.setAttribute("f_dc_1",  new THREE.BufferAttribute(fdc1, 1));
    if (fdc2)   geom.setAttribute("f_dc_2",  new THREE.BufferAttribute(fdc2, 1));
    if (opacity) geom.setAttribute("opacity", new THREE.BufferAttribute(opacity, 1));

    // 디버깅용: 어떤 attribute들이 들어왔는지 출력하고 싶으면 여기서
    // for (const name in geom.attributes) {
    //   const attr = geom.getAttribute(name);
    //   console.log("geom attr:", name, "itemSize =", attr.itemSize, "count =", attr.count);
    // }

    return geom;
  }
}
