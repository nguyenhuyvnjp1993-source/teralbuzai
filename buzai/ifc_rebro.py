"""Ghi IFC4 cho một 部材, theo cấu trúc file Rebro xuất (BSJ_MEP_*).

Cấu trúc bắt chước 2 file mẫu Rebro 2026 (新規図面12.ifc, 接続.ifc):
- IfcDistributionElement, ObjectType '機器・器具.ユーザー部材'
- hình qua IfcMappedItem -> IfcRepresentationMap
- 接続口 là text trong pset BSJ_MEP_Common.connecting_point_1..4.
  Mỗi đầu nối 14 trường: x,y,z,cỡ,0,0,mã,0,hx,hy,hz,0,0,0 (toạ độ thế giới, mm);
  các đầu nối cùng nhóm nối tiếp nhau bằng dấu phẩy.
"""
from __future__ import annotations

import datetime as _dt
import time
from dataclasses import dataclass, field

import ifcopenshell
import ifcopenshell.guid

from .geom import Luoi


@dataclass
class DauNoi:
    """Một 接続口."""
    vi_tri: tuple          # (x, y, z) mm, toạ độ cục bộ của 部材
    co: int                # 呼び径 (A)
    huong: tuple           # vector hướng ra ngoài
    ma: str = "A20"        # mã trong trường thứ 7 (xem docs)
    nhom: int = 2          # connecting_point_<nhom>

    def chuoi(self, goc=(0.0, 0.0, 0.0)) -> str:
        x, y, z = (self.vi_tri[i] + goc[i] for i in range(3))
        hx, hy, hz = self.huong
        f = lambda v: f"{v:.6f}"
        return ",".join([f(x), f(y), f(z), str(self.co), "0", "0", self.ma, "0",
                         f(hx), f(hy), f(hz), f(0), f(0), f(0)])


@dataclass
class ThongTinBuzai:
    ten_kieu: str                       # 型式名称 (NAME2)
    ma_hang: str                        # メーカー型番 (NAME1)
    ma_phan_loai: str = "50908000000000"  # 機器分類コード (CGRYCODE); mẫu Rebro: その他特殊設備
    dau_noi: list = field(default_factory=list)
    mau: tuple = (0.5, 0.5, 0.5)


def _sv(f, ten, gt):
    return f.create_entity("IfcPropertySingleValue", Name=ten, Description="",
                           NominalValue=f.create_entity("IfcText", gt))


def _lv(f, ten, ma, gt):
    return f.create_entity("IfcPropertyListValue", Name=ten, Description="",
                           ListValues=[f.create_entity("IfcText", v) for v in (ma, gt, ten, "", "")])


def ghi_ifc(duong_dan: str, tt: ThongTinBuzai, luois: list[Luoi], kieu_hinh: str = "tess",
            goc=(0.0, 0.0, 0.0)) -> None:
    f = ifcopenshell.file(schema="IFC4")
    now = _dt.datetime.now()
    g = ifcopenshell.guid.new

    org = f.create_entity("IfcOrganization", Name="teralbuzai")
    app = f.create_entity("IfcApplication", ApplicationDeveloper=org, Version="0.1",
                          ApplicationFullName="teralbuzai", ApplicationIdentifier="teralbuzai")
    person = f.create_entity("IfcPerson", FamilyName="", GivenName="")
    po = f.create_entity("IfcPersonAndOrganization", ThePerson=person, TheOrganization=org)
    oh = f.create_entity("IfcOwnerHistory", OwningUser=po, OwningApplication=app, ChangeAction="NOCHANGE",
                         CreationDate=int(time.time()))

    P = lambda *c: f.create_entity("IfcCartesianPoint", Coordinates=[float(x) for x in c])
    Dn = lambda *c: f.create_entity("IfcDirection", DirectionRatios=[float(x) for x in c])
    goc0 = P(0, 0, 0)
    ax = f.create_entity("IfcAxis2Placement3D", Location=goc0, Axis=Dn(0, 0, 1), RefDirection=Dn(1, 0, 0))
    ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model", CoordinateSpaceDimension=3,
                          Precision=1e-5, WorldCoordinateSystem=ax, TrueNorth=Dn(0, 1))

    units = f.create_entity("IfcUnitAssignment", Units=[
        f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Prefix="MILLI", Name="METRE"),
        f.create_entity("IfcSIUnit", UnitType="AREAUNIT", Name="SQUARE_METRE"),
        f.create_entity("IfcSIUnit", UnitType="VOLUMEUNIT", Name="CUBIC_METRE"),
        f.create_entity("IfcSIUnit", UnitType="PLANEANGLEUNIT", Name="RADIAN"),
    ])
    proj = f.create_entity("IfcProject", GlobalId=g(), OwnerHistory=oh, Name="Default Project",
                           RepresentationContexts=[ctx], UnitsInContext=units)
    lp_site = f.create_entity("IfcLocalPlacement", RelativePlacement=ax)
    lp_bld = f.create_entity("IfcLocalPlacement", PlacementRelTo=lp_site, RelativePlacement=ax)
    lp_sto = f.create_entity("IfcLocalPlacement", PlacementRelTo=lp_bld, RelativePlacement=ax)
    site = f.create_entity("IfcSite", GlobalId=g(), OwnerHistory=oh, Name="Default Site", ObjectPlacement=lp_site,
                           CompositionType="ELEMENT")
    bld = f.create_entity("IfcBuilding", GlobalId=g(), OwnerHistory=oh, Name="Default Building",
                          ObjectPlacement=lp_bld, CompositionType="ELEMENT")
    sto = f.create_entity("IfcBuildingStorey", GlobalId=g(), OwnerHistory=oh, Name="1FL", ObjectPlacement=lp_sto,
                          CompositionType="ELEMENT", Elevation=0.0)
    f.create_entity("IfcRelAggregates", GlobalId=g(), OwnerHistory=oh, RelatingObject=proj, RelatedObjects=[site])
    f.create_entity("IfcRelAggregates", GlobalId=g(), OwnerHistory=oh, RelatingObject=site, RelatedObjects=[bld])
    f.create_entity("IfcRelAggregates", GlobalId=g(), OwnerHistory=oh, RelatingObject=bld, RelatedObjects=[sto])

    # màu
    r, gg, b = tt.mau
    col = f.create_entity("IfcColourRgb", Red=r, Green=gg, Blue=b)
    rend = f.create_entity("IfcSurfaceStyleRendering", SurfaceColour=col, Transparency=0.0, ReflectanceMethod="NOTDEFINED")
    style = f.create_entity("IfcSurfaceStyle", Name="Color", Side="BOTH", Styles=[rend])

    items = []
    for m in luois:
        if kieu_hinh == "brep":
            pts = [P(*p) for p in m.v]
            faces = [f.create_entity("IfcFace", Bounds=[f.create_entity(
                "IfcFaceOuterBound", Bound=f.create_entity("IfcPolyLoop", Polygon=[pts[i] for i in tri]),
                Orientation=True)]) for tri in m.f]
            it = f.create_entity("IfcFacetedBrep", Outer=f.create_entity("IfcClosedShell", CfsFaces=faces))
        else:
            pl = f.create_entity("IfcCartesianPointList3D", CoordList=[[float(c) for c in p] for p in m.v])
            it = f.create_entity("IfcTriangulatedFaceSet", Coordinates=pl, Closed=True,
                                 CoordIndex=[[int(i) + 1 for i in tri] for tri in m.f])
        f.create_entity("IfcStyledItem", Item=it, Styles=[style])
        items.append(it)
    rep_type = "Brep" if kieu_hinh == "brep" else "Tessellation"
    body = f.create_entity("IfcShapeRepresentation", ContextOfItems=ctx, RepresentationIdentifier="Body",
                           RepresentationType=rep_type, Items=items)
    rmap = f.create_entity("IfcRepresentationMap", MappingOrigin=ax, MappedRepresentation=body)
    mi = f.create_entity("IfcMappedItem", MappingSource=rmap, MappingTarget=f.create_entity(
        "IfcCartesianTransformationOperator3D", LocalOrigin=goc0))
    f.create_entity("IfcStyledItem", Item=mi, Styles=[style])
    srep = f.create_entity("IfcShapeRepresentation", ContextOfItems=ctx, RepresentationIdentifier="Body",
                           RepresentationType="MappedRepresentation", Items=[mi])
    pds = f.create_entity("IfcProductDefinitionShape", Name="", Description="", Representations=[srep])

    lp_el = f.create_entity("IfcLocalPlacement", PlacementRelTo=lp_sto, RelativePlacement=f.create_entity(
        "IfcAxis2Placement3D", Location=P(*goc), Axis=Dn(0, 0, 1), RefDirection=Dn(1, 0, 0)))
    ten = f"【その他（ユーザー部材）】{tt.ten_kieu} {tt.ma_hang}"
    el = f.create_entity("IfcDistributionElement", GlobalId=g(), OwnerHistory=oh, Name=ten,
                         Description="機器・器具.ユーザー部材", ObjectPlacement=lp_el, Representation=pds)
    f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=g(), OwnerHistory=oh,
                    Name="BuildingStoreyContainer", RelatedElements=[el], RelatingStructure=sto)

    # ---- psets theo mẫu Rebro
    nhom = {1: [], 2: [], 3: [], 4: []}
    for d in tt.dau_noi:
        nhom[d.nhom].append(d.chuoi(goc))
    sp = lambda x: f"{x:.6f}"
    common = [
        _sv(f, "version", "7"), _sv(f, "pset_version", "2"), _sv(f, "vender_version", "12.0.0.13"),
        _sv(f, "data_class", "K"), _sv(f, "sequence_number", "00001"), _sv(f, "vender_code", "NS"),
        _sv(f, "output_date", now.strftime("%Y%m%d")), _sv(f, "output_time", now.strftime("%H%M")),
        _sv(f, "output_layer", ""), _sv(f, "system_name", tt.ten_kieu), _sv(f, "route_sign", ""),
        _sv(f, "setting_basis_point", ",".join(sp(c) for c in goc)),
    ] + [_sv(f, f"connecting_point_{i}", ",".join(nhom[i])) for i in (1, 2, 3, 4)] + [
        _sv(f, "main_vector", "1.000000,0.000000,0.000000"),
        _sv(f, "sub_vector", "0.000000,-1.000000,0.000000"),
    ]
    psets = [
        f.create_entity("IfcPropertySet", GlobalId=g(), OwnerHistory=oh, Name="BSJ_MEP_Common", HasProperties=common),
        f.create_entity("IfcPropertySet", GlobalId=g(), OwnerHistory=oh, Name="BSJ_MEP_EquipmentCommon",
                        HasProperties=[_sv(f, "parts_number", "")]),
        f.create_entity("IfcPropertySet", GlobalId=g(), OwnerHistory=oh, Name="BSJ_MEP_EquipmentData", HasProperties=[
            f.create_entity("IfcComplexProperty", Name="property_data", UsageName="機器属性", HasProperties=[
                _lv(f, "仕様バージョンコード", "SPVER", "10")]),
            f.create_entity("IfcComplexProperty", Name="table_data", UsageName="機器表属性", HasProperties=[
                _lv(f, "仕様バージョンコード", "SPVER", "10"),
                _lv(f, "機器分類コード", "CGRYCODE", tt.ma_phan_loai),
                _lv(f, "型式名称", "NAME2", tt.ten_kieu),
                _lv(f, "メーカー型番", "NAME1", tt.ma_hang)]),
        ]),
        f.create_entity("IfcPropertySet", GlobalId=g(), OwnerHistory=oh, Name="BSJ_MEP_EstimateData", HasProperties=[
            _sv(f, "construction_place_code", "100"), _sv(f, "construction_place_name", "施工区分未設定")]),
    ]
    for ps in psets:
        f.create_entity("IfcRelDefinesByProperties", GlobalId=g(), OwnerHistory=oh, RelatedObjects=[el],
                        RelatingPropertyDefinition=ps)
    f.write(duong_dan)
